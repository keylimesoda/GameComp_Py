import json
import sqlite3

from gamecompanion.rag import (
    _build_rag_context,
    _cosine_sim,
    _rag_index_message,
    _rag_retrieve,
    _tokenize,
    _vectorize,
)


def _make_db(db_path):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            playthrough_id INTEGER NOT NULL
        );
        CREATE TABLE rag_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens_json TEXT NOT NULL
        );
        """
    )
    return db


def test_tokenize_vectorize_and_cosine_similarity():
    tokens = _tokenize("The Hero enters the dungeon and finds 2 keys")
    assert "the" not in tokens
    assert "hero" in tokens and "dungeon" in tokens
    assert "2" not in tokens  # single-char tokens are filtered

    v1 = _vectorize("red dragon dragon")
    v2 = _vectorize("dragon red")
    assert v1["dragon"] == 2
    sim = _cosine_sim(v1, v2)
    assert 0.99 > sim > 0.7
    assert _cosine_sim(_vectorize(""), v2) == 0.0


def test_rag_index_retrieve_and_context_excludes_recent(tmp_path):
    db = _make_db(tmp_path / "rag.sqlite")
    pid = 3

    for mid in range(1, 16):
        db.execute("INSERT INTO messages(id, playthrough_id) VALUES (?, ?)", (mid, pid))

    _rag_index_message(db, pid, 1, "assistant", "A red dragon sleeps in the mountain cave")
    _rag_index_message(db, pid, 2, "assistant", "The village blacksmith can forge silver swords")
    _rag_index_message(db, pid, 12, "assistant", "Recent chatter about market prices")
    db.commit()

    row = db.execute("SELECT tokens_json FROM rag_chunks WHERE message_id = 1").fetchone()
    parsed = json.loads(row["tokens_json"])
    assert parsed["dragon"] == 1

    hits = _rag_retrieve(db, pid, "Where is the dragon cave?")
    assert hits
    assert "dragon" in hits[0].lower()

    context = _build_rag_context(db, pid, "What about market prices?")
    assert "market prices" not in context.lower()
