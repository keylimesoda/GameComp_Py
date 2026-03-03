import sqlite3

from gamecompanion.graph import (
    _add_edge,
    _apply_graph_deltas,
    _get_all_edges,
    _get_all_nodes,
    _get_node,
    _remove_edge,
    _remove_node,
    _upsert_node,
)


def _make_db(db_path):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE graph_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            properties_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'active',
            updated_at TEXT,
            UNIQUE(playthrough_id, name)
        );
        CREATE TABLE graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id INTEGER NOT NULL,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            properties_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE(playthrough_id, source_id, target_id, label)
        );
        """
    )
    return db


def test_node_crud_and_edge_lifecycle(tmp_path):
    db = _make_db(tmp_path / "graph.sqlite")
    pid = 1

    _upsert_node(db, pid, "Alice", "character", {"hp": 10})
    db.commit()
    node = _get_node(db, pid, "Alice")
    assert node["kind"] == "character"
    assert node["properties"]["hp"] == 10

    _upsert_node(db, pid, "Alice", "character", {"hp": 12}, status="inactive")
    _upsert_node(db, pid, "Forest", "world", {"zone": "north"})
    db.commit()
    assert _get_node(db, pid, "Alice")["status"] == "inactive"

    _add_edge(db, pid, "Alice", "Forest", "located_in", {"since": "day1"})
    db.commit()
    edges = _get_all_edges(db, pid)
    assert len(edges) == 1
    assert edges[0]["source"] == "Alice"
    assert edges[0]["target"] == "Forest"

    _remove_edge(db, pid, "Alice", "Forest", "located_in")
    db.commit()
    assert _get_all_edges(db, pid) == []

    _add_edge(db, pid, "Alice", "Forest", "located_in")
    db.commit()
    _remove_node(db, pid, "Alice")
    db.commit()
    assert _get_node(db, pid, "Alice") is None
    assert _get_all_edges(db, pid) == []


def test_apply_graph_deltas_updates_nodes_lists_and_edges(tmp_path):
    db = _make_db(tmp_path / "graph2.sqlite")
    pid = 7

    deltas = [
        {"operation": "upsert_node", "name": "Quest1", "kind": "quest", "properties": {"state": "open"}},
        {"operation": "update_property", "name": "Quest1", "property": "meta.stage", "value": 2},
        {"operation": "add_to_list", "name": "Quest1", "property": "tags", "value": "main"},
        {"operation": "upsert_node", "name": "Town", "kind": "world", "properties": {}},
        {"operation": "add_edge", "source": "Quest1", "target": "Town", "label": "happens_in"},
        {"operation": "remove_edge", "source": "Quest1", "target": "Town", "label": "happens_in"},
    ]

    applied = _apply_graph_deltas(db, pid, deltas)
    db.commit()

    assert applied == len(deltas)
    quest = _get_node(db, pid, "Quest1")
    assert quest["properties"]["meta"]["stage"] == 2
    assert "main" in quest["properties"]["tags"]
    assert _get_all_edges(db, pid) == []
    assert len(_get_all_nodes(db, pid)) == 2
