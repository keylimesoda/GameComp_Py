import sqlite3

from gamecompanion import memory


def _mk_ctx():
    return {
        "nodes": [
            {
                "name": "Aria",
                "kind": "character",
                "properties": {
                    "role": "protagonist",
                    "class": "Ranger",
                    "level": 10,
                    "DEX": 18,
                },
                "status": "active",
            },
            {
                "name": "Borin",
                "kind": "character",
                "properties": {"class": "Cleric", "level": 9},
                "status": "active",
            },
        ],
        "edges": [],
    }


def test_build_character_sheet_returns_expected_lines():
    sheet = memory._build_character_sheet(_mk_ctx(), "aria")
    assert sheet is not None
    assert "Character Sheet - Aria" in sheet
    assert "Class: Ranger" in sheet
    assert "level 10" in sheet
    assert "DEX 18" in sheet


def test_build_party_summary_lists_characters():
    summary = memory._build_party_summary(_mk_ctx())
    assert summary.startswith("Party Summary:")
    assert "- Aria" in summary
    assert "- Borin" in summary


def test_memory_query_response_handles_party_and_missing_sheet():
    ctx = _mk_ctx()
    resp = memory._build_memory_query_response("what do you remember about my party", ctx)
    assert resp and "Party Summary:" in resp

    resp2 = memory._build_memory_query_response("show me Cora's stats", ctx)
    assert "I don't have stats for Cora yet." == resp2


def test_load_stable_context_reads_nodes_and_edges_from_sqlite():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE graph_nodes (id INTEGER PRIMARY KEY, playthrough_id INT, name TEXT, kind TEXT, properties_json TEXT, status TEXT)")
    db.execute("CREATE TABLE graph_edges (id INTEGER PRIMARY KEY, playthrough_id INT, source_id INT, target_id INT, label TEXT, properties_json TEXT)")
    db.execute("INSERT INTO graph_nodes (id, playthrough_id, name, kind, properties_json, status) VALUES (1, 1, 'Aria', 'character', '{\"level\": 10}', 'active')")
    db.execute("INSERT INTO graph_nodes (id, playthrough_id, name, kind, properties_json, status) VALUES (2, 1, 'Borin', 'character', '{\"level\": 9}', 'active')")
    db.execute("INSERT INTO graph_edges (playthrough_id, source_id, target_id, label, properties_json) VALUES (1, 1, 2, 'knows', '{}')")

    ctx = memory._load_stable_context(db, 1)
    assert len(ctx["nodes"]) == 2
    assert len(ctx["edges"]) == 1
    assert ctx["edges"][0]["source"] == "Aria"
