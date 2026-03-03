import asyncio
import io
import json
import sqlite3
import zipfile

from starlette.datastructures import UploadFile

from gamecompanion import export as export_mod


def test_export_playthrough_writes_expected_zip(monkeypatch):
    class FakeDB:
        def execute(self, q, params=()):
            class C:
                def fetchone(self_non):
                    return {"id": 1, "name": "Run", "game_title": "ER", "created_at": "", "updated_at": ""}

                def fetchall(self_non):
                    return [{"role": "user", "content": "hello", "created_at": ""}]

            return C()

        def close(self):
            return None

    monkeypatch.setattr(export_mod, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(export_mod, "_load_stable_context", lambda db, pid: {"nodes": [], "edges": []})

    resp = export_mod.export_playthrough(1)
    assert resp.media_type == "application/zip"

    # body_iterator is an async generator; consume it synchronously
    async def _read_body():
        body = b""
        async for chunk in resp.body_iterator:
            body += chunk if isinstance(chunk, bytes) else chunk.encode()
        return body

    body = asyncio.run(_read_body())
    zf = zipfile.ZipFile(io.BytesIO(body), "r")
    names = set(zf.namelist())
    assert "playthrough.json" in names
    assert "messages.json" in names
    assert "stable_context.json" in names


class _NoCloseConnection:
    """Wrapper that prevents close() from actually closing the connection."""
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        if name == "close":
            return lambda: None
        return getattr(self._conn, name)


def test_import_playthrough_inserts_data(monkeypatch):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE playthroughs (id INTEGER PRIMARY KEY, name TEXT, game_title TEXT)")
    db.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, playthrough_id INT, role TEXT, content TEXT)")

    wrapper = _NoCloseConnection(db)
    monkeypatch.setattr(export_mod, "_get_db", lambda: wrapper)
    monkeypatch.setattr(export_mod, "_upsert_node", lambda *a, **k: None)
    monkeypatch.setattr(export_mod, "_add_edge", lambda *a, **k: None)
    monkeypatch.setattr(export_mod, "_rag_index_message", lambda *a, **k: None)

    payload = {
        "playthrough": {"name": "Run", "game_title": "ER"},
        "messages": [{"role": "user", "content": "hello"}],
        "stable_context": {"nodes": [], "edges": []},
    }
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("playthrough.json", json.dumps(payload["playthrough"]))
        zf.writestr("messages.json", json.dumps(payload["messages"]))
        zf.writestr("stable_context.json", json.dumps(payload["stable_context"]))
    bio.seek(0)

    upload = UploadFile(filename="import.zip", file=bio)
    new_id = export_mod.import_playthrough(upload)
    assert isinstance(new_id, int)
    rows = db.execute("SELECT role, content FROM messages WHERE playthrough_id = ?", (new_id,)).fetchall()
    assert len(rows) == 1
    assert rows[0]["content"] == "hello"
    db.close()
