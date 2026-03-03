from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# Database configuration mirrors main.py defaults
DATA_DIR = Path(os.environ.get("GAMECOMPANION_DATA_DIR", "data"))
DB_PATH = DATA_DIR / "gamecompanion.db"


def ensure_tables(db_path: Path = DB_PATH):
    """Create and migrate SQLite schema if it does not exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS playthroughs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            game_title  TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id  INTEGER NOT NULL REFERENCES playthroughs(id),
            role            TEXT    NOT NULL,
            content         TEXT    NOT NULL,
            created_at      TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS rag_chunks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id  INTEGER NOT NULL REFERENCES playthroughs(id),
            message_id      INTEGER NOT NULL REFERENCES messages(id),
            role            TEXT    NOT NULL,
            content         TEXT    NOT NULL,
            tokens_json     TEXT    NOT NULL,
            created_at      TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id  INTEGER NOT NULL REFERENCES playthroughs(id),
            name            TEXT    NOT NULL,
            kind            TEXT    NOT NULL,
            properties_json TEXT    NOT NULL DEFAULT '{}',
            status          TEXT    DEFAULT 'active',
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE(playthrough_id, name)
        );
        CREATE TABLE IF NOT EXISTS graph_edges (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            playthrough_id  INTEGER NOT NULL REFERENCES playthroughs(id),
            source_id       INTEGER NOT NULL REFERENCES graph_nodes(id),
            target_id       INTEGER NOT NULL REFERENCES graph_nodes(id),
            label           TEXT    NOT NULL,
            properties_json TEXT    NOT NULL DEFAULT '{}',
            created_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE(playthrough_id, source_id, target_id, label)
        );
        """
    )
    con.close()


def get_db() -> sqlite3.Connection:
    """Return a SQLite connection with Row factory enabled."""
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con
