from __future__ import annotations

import json
import sqlite3
from datetime import datetime


def _get_node(db: sqlite3.Connection, playthrough_id: int, name: str) -> dict | None:
    """Retrieve a single graph node by name. Returns dict with name/kind/properties or None."""
    row = db.execute(
        "SELECT name, kind, properties_json, status FROM graph_nodes "
        "WHERE playthrough_id = ? AND name = ?",
        (playthrough_id, name),
    ).fetchone()
    if not row:
        return None
    return {
        "name": row["name"],
        "kind": row["kind"],
        "properties": json.loads(row["properties_json"]),
        "status": row["status"],
    }


def _upsert_node(
    db: sqlite3.Connection,
    playthrough_id: int,
    name: str,
    kind: str,
    properties: dict,
    status: str = "active",
):
    """Create or update a graph node."""
    db.execute(
        """
        INSERT INTO graph_nodes (playthrough_id, name, kind, properties_json, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(playthrough_id, name)
        DO UPDATE SET kind = excluded.kind,
                      properties_json = excluded.properties_json,
                      status = excluded.status,
                      updated_at = datetime('now')
        """,
        (playthrough_id, name, kind, json.dumps(properties, ensure_ascii=False), status),
    )


def _get_nodes_by_kind(db: sqlite3.Connection, playthrough_id: int, kind: str) -> list[dict]:
    """Return all nodes of a given kind for a playthrough."""
    rows = db.execute(
        "SELECT name, kind, properties_json, status FROM graph_nodes "
        "WHERE playthrough_id = ? AND kind = ?",
        (playthrough_id, kind),
    ).fetchall()
    return [
        {
            "name": r["name"],
            "kind": r["kind"],
            "properties": json.loads(r["properties_json"]),
            "status": r["status"],
        }
        for r in rows
    ]


def _get_all_nodes(db: sqlite3.Connection, playthrough_id: int) -> list[dict]:
    """Return every node for a playthrough."""
    rows = db.execute(
        "SELECT name, kind, properties_json, status FROM graph_nodes "
        "WHERE playthrough_id = ?",
        (playthrough_id,),
    ).fetchall()
    return [
        {
            "name": r["name"],
            "kind": r["kind"],
            "properties": json.loads(r["properties_json"]),
            "status": r["status"],
        }
        for r in rows
    ]


def _get_all_edges(db: sqlite3.Connection, playthrough_id: int) -> list[dict]:
    """Return every edge for a playthrough, with source/target names."""
    rows = db.execute(
        "SELECT s.name AS source, t.name AS target, e.label, e.properties_json "
        "FROM graph_edges e "
        "JOIN graph_nodes s ON e.source_id = s.id "
        "JOIN graph_nodes t ON e.target_id = t.id "
        "WHERE e.playthrough_id = ?",
        (playthrough_id,),
    ).fetchall()
    return [
        {
            "source": r["source"],
            "target": r["target"],
            "label": r["label"],
            "properties": json.loads(r["properties_json"]),
        }
        for r in rows
    ]


def _add_edge(
    db: sqlite3.Connection,
    playthrough_id: int,
    source_name: str,
    target_name: str,
    label: str,
    properties: dict | None = None,
):
    """Create an edge between two nodes (both must exist)."""
    src = db.execute(
        "SELECT id FROM graph_nodes WHERE playthrough_id = ? AND name = ?",
        (playthrough_id, source_name),
    ).fetchone()
    tgt = db.execute(
        "SELECT id FROM graph_nodes WHERE playthrough_id = ? AND name = ?",
        (playthrough_id, target_name),
    ).fetchone()
    if not src or not tgt:
        return
    db.execute(
        """
        INSERT OR IGNORE INTO graph_edges
            (playthrough_id, source_id, target_id, label, properties_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (playthrough_id, src["id"], tgt["id"], label, json.dumps(properties or {}, ensure_ascii=False)),
    )


def _remove_edge(
    db: sqlite3.Connection,
    playthrough_id: int,
    source_name: str,
    target_name: str,
    label: str,
):
    """Remove an edge between two nodes."""
    db.execute(
        """
        DELETE FROM graph_edges
        WHERE playthrough_id = ?
          AND source_id = (SELECT id FROM graph_nodes WHERE playthrough_id = ? AND name = ?)
          AND target_id = (SELECT id FROM graph_nodes WHERE playthrough_id = ? AND name = ?)
          AND label = ?
        """,
        (playthrough_id, playthrough_id, source_name, playthrough_id, target_name, label),
    )


def _remove_node(db: sqlite3.Connection, playthrough_id: int, name: str):
    """Delete a node and all its edges."""
    node = db.execute(
        "SELECT id FROM graph_nodes WHERE playthrough_id = ? AND name = ?",
        (playthrough_id, name),
    ).fetchone()
    if not node:
        return
    nid = node["id"]
    db.execute(
        "DELETE FROM graph_edges WHERE playthrough_id = ? AND (source_id = ? OR target_id = ?)",
        (playthrough_id, nid, nid),
    )
    db.execute("DELETE FROM graph_nodes WHERE id = ?", (nid,))


def _update_json_path(target: dict, path: str, value):
    parts = path.split(".")
    cur = target
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def _add_json_path(target: dict, path: str, value):
    parts = path.split(".")
    cur = target
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    if parts[-1] not in cur or not isinstance(cur[parts[-1]], list):
        cur[parts[-1]] = []
    if value not in cur[parts[-1]]:
        cur[parts[-1]].append(value)


def _apply_graph_deltas(
    db: sqlite3.Connection,
    playthrough_id: int,
    deltas: list[dict],
) -> int:
    """Apply graph context deltas. Returns number of deltas applied."""
    applied = 0
    for d in deltas or []:
        op = d.get("operation")

        if op == "upsert_node":
            name = d.get("name")
            kind = d.get("kind")
            if not name or not kind:
                continue
            existing = _get_node(db, playthrough_id, name)
            if existing:
                merged = existing["properties"].copy()
                merged.update(d.get("properties") or {})
                _upsert_node(db, playthrough_id, name, kind, merged, d.get("status", existing.get("status", "active")))
            else:
                _upsert_node(db, playthrough_id, name, kind, d.get("properties") or {}, d.get("status", "active"))
            applied += 1

        elif op == "update_property":
            name = d.get("name")
            prop = d.get("property")
            if not name or not prop:
                continue
            node = _get_node(db, playthrough_id, name)
            if not node:
                kind = "narrative" if name == "__narrative__" else "codex" if name == "__codex__" else "world" if name == "__world__" else "character"
                _upsert_node(db, playthrough_id, name, kind, {})
                node = _get_node(db, playthrough_id, name)
            props = node["properties"]
            _update_json_path(props, prop, d.get("value"))
            _upsert_node(db, playthrough_id, name, node["kind"], props)
            applied += 1

        elif op == "add_to_list":
            name = d.get("name")
            prop = d.get("property")
            if not name or not prop:
                continue
            node = _get_node(db, playthrough_id, name)
            if not node:
                kind = "narrative" if name == "__narrative__" else "codex" if name == "__codex__" else "world" if name == "__world__" else "misc"
                _upsert_node(db, playthrough_id, name, kind, {})
                node = _get_node(db, playthrough_id, name)
            props = node["properties"]
            _add_json_path(props, prop, d.get("value"))
            _upsert_node(db, playthrough_id, name, node["kind"], props)
            applied += 1

        elif op == "add_edge":
            src = d.get("source")
            tgt = d.get("target")
            label = d.get("label")
            if src and tgt and label:
                _add_edge(db, playthrough_id, src, tgt, label, d.get("properties"))
                applied += 1

        elif op == "remove_edge":
            src = d.get("source")
            tgt = d.get("target")
            label = d.get("label")
            if src and tgt and label:
                _remove_edge(db, playthrough_id, src, tgt, label)
                applied += 1

        elif op == "remove_node":
            name = d.get("name")
            if name:
                _remove_node(db, playthrough_id, name)
                applied += 1

    return applied


def _append_graph_changelog(data_dir, playthrough_id: int, deltas: list[dict]):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "playthrough_id": playthrough_id,
        "deltas": deltas,
    }
    path = data_dir / "changelog.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
