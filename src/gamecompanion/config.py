"""Configuration helpers and constants for LoreKeeper/GameCompanion."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Core runtime configuration from environment variables
PORT = int(os.environ.get("GAMECOMPANION_PORT", "5001"))
DATA_DIR = Path(os.environ.get("GAMECOMPANION_DATA_DIR", "data"))
TEST_MODE = os.environ.get("GAMECOMPANION_TEST_MODE") == "1"

# Derived filesystem paths
DB_PATH = DATA_DIR / "gamecompanion.db"
CONFIG_PATH = DATA_DIR / "config.json"
CHANGELOG_PATH = DATA_DIR / "changelog.jsonl"

# App-level settings defaults
DEFAULT_MODEL_NAME = "gpt-4o"
DEFAULT_RECENT_WINDOW_SIZE = 10
DEFAULT_RAG_TOP_K = 3


def load_config() -> dict:
    """Load JSON configuration from disk, returning an empty dict if missing."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def save_config(cfg: dict) -> None:
    """Persist JSON configuration to disk, creating directories as needed."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg))


def ensure_data_dir() -> None:
    """Ensure the configured data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
