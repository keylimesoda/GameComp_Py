import importlib
import sqlite3


def test_ensure_tables_creates_schema(tmp_path):
    import gamecompanion.db as db
    importlib.reload(db)

    db_path = tmp_path / "unit.db"
    db.ensure_tables(db_path)

    con = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        con.close()

    expected = {
        "playthroughs",
        "messages",
        "rag_chunks",
        "graph_nodes",
        "graph_edges",
    }
    assert expected.issubset(tables)


def test_get_db_uses_env_db_path_and_row_factory(monkeypatch, tmp_path):
    monkeypatch.setenv("GAMECOMPANION_DATA_DIR", str(tmp_path))

    import gamecompanion.db as db
    importlib.reload(db)

    db.ensure_tables()
    con = db.get_db()
    try:
        assert con.row_factory is sqlite3.Row

        # Verify DB file used by module-level DB_PATH exists at env-derived location
        assert (tmp_path / "gamecompanion.db").exists()
    finally:
        con.close()
