"""Unit tests for auth.py — GitHub OAuth Device Flow."""

import json
import tempfile
from pathlib import Path

from gamecompanion.auth import save_token, load_token, validate_token


def test_save_and_load_token():
    """Token round-trips through save/load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        save_token("ghp_test_token_123", data_dir)
        loaded = load_token(data_dir)
        assert loaded == "ghp_test_token_123"


def test_load_token_missing():
    """Returns None when no token file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assert load_token(Path(tmpdir)) is None


def test_load_token_corrupted():
    """Returns None for corrupted token file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        (data_dir / "github_token.json").write_text("not json{{{")
        assert load_token(data_dir) is None


def test_save_token_file_permissions():
    """Token file should have restricted permissions on Unix."""
    import stat
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        save_token("test", data_dir)
        token_path = data_dir / "github_token.json"
        mode = stat.S_IMODE(token_path.stat().st_mode)
        assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"


def test_validate_token_rejects_garbage():
    """Invalid token should fail validation."""
    assert validate_token("not-a-real-token") is False
