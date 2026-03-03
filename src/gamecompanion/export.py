from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from starlette.responses import StreamingResponse
from starlette.datastructures import UploadFile

from .db import get_db as _get_db
from .memory import _load_stable_context
from .graph import _upsert_node, _add_edge
from .rag import _rag_index_message


def export_playthrough(playthrough_id: int):
    """Export a playthrough (metadata, messages, stable context) as a ZIP download."""
    db = _get_db()
    pt = db.execute(
        "SELECT id, name, game_title, created_at, updated_at FROM playthroughs WHERE id = ?",
        (playthrough_id,),
    ).fetchone()
    msgs = db.execute(
        "SELECT role, content, created_at FROM messages WHERE playthrough_id = ? ORDER BY created_at",
        (playthrough_id,),
    ).fetchall()
    stable_context = _load_stable_context(db, playthrough_id)
    db.close()

    payload = {
        "playthrough": dict(pt) if pt else {},
        "messages": [dict(m) for m in msgs],
        "stable_context": stable_context,
    }

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("playthrough.json", json.dumps(payload["playthrough"]))
        zf.writestr("messages.json", json.dumps(payload["messages"]))
        zf.writestr("stable_context.json", json.dumps(payload["stable_context"]))
    mem.seek(0)

    filename = f"playthrough_{playthrough_id}.zip"
    return StreamingResponse(
        mem,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def import_playthrough(import_file: UploadFile):
    """Import a playthrough ZIP and recreate playthrough, graph, and message data."""
    data = import_file.file.read()
    mem = io.BytesIO(data)
    with zipfile.ZipFile(mem, "r") as zf:
        playthrough = json.loads(zf.read("playthrough.json"))
        messages = json.loads(zf.read("messages.json"))
        stable_context = json.loads(zf.read("stable_context.json"))

    db = _get_db()
    name = playthrough.get("name", "Imported Playthrough")
    game_title = playthrough.get("game_title", "")
    existing = db.execute("SELECT id FROM playthroughs WHERE name = ?", (name,)).fetchone()
    if existing:
        name = f"{name} (Imported)"

    cur = db.execute(
        "INSERT INTO playthroughs (name, game_title) VALUES (?, ?)",
        (name, game_title),
    )
    db.commit()
    playthrough_id = cur.lastrowid

    for node in stable_context.get("nodes", []) or []:
        _upsert_node(
            db,
            playthrough_id,
            node["name"],
            node["kind"],
            node.get("properties", {}),
            node.get("status", "active"),
        )
    for edge in stable_context.get("edges", []) or []:
        _add_edge(
            db,
            playthrough_id,
            edge["source"],
            edge["target"],
            edge["label"],
            edge.get("properties", {}),
        )

    for m in messages:
        cur = db.execute(
            "INSERT INTO messages (playthrough_id, role, content) VALUES (?, ?, ?)",
            (playthrough_id, m.get("role", "user"), m.get("content", "")),
        )
        msg_id = cur.lastrowid
        _rag_index_message(
            db,
            playthrough_id,
            msg_id,
            m.get("role", "user"),
            m.get("content", ""),
        )

    db.commit()
    db.close()
    return playthrough_id
