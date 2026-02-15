"""E2E test infrastructure for LoreKeeper.

Starts the FastHTML application server in test mode and provides
fixtures for Playwright browser tests.

Environment variables used by the server in test mode:
  GAMECOMPANION_TEST_MODE=1  →  enables mock LLM & /test/reset endpoint
  GAMECOMPANION_DATA_DIR     →  writable temp directory for DB + config
  GAMECOMPANION_PORT         →  HTTP port (avoids conflict with dev server)
"""

import os
import sys
import time
import subprocess

import pytest
import httpx

# Non-standard port so tests don't collide with a running dev server
TEST_PORT = 5199
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

# Project root is three levels up from tests/e2e/conftest.py
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


@pytest.fixture(scope="session")
def _data_dir(tmp_path_factory):
    """Session-scoped temporary directory for app data (SQLite DB, config)."""
    return str(tmp_path_factory.mktemp("gamecompanion_data"))


@pytest.fixture(scope="session")
def app_url(_data_dir):
    """Start the LoreKeeper server in test mode for the entire session.

    Yields the base URL (e.g. http://127.0.0.1:5199).
    Tears down the server after all tests complete.
    """
    env = os.environ.copy()
    env["GAMECOMPANION_TEST_MODE"] = "1"
    env["GAMECOMPANION_DATA_DIR"] = _data_dir
    env["GAMECOMPANION_PORT"] = str(TEST_PORT)
    env["PYTHONUNBUFFERED"] = "1"  # flush output immediately for log readability

    # Server log files for debugging test failures
    stdout_path = os.path.join(_data_dir, "server.stdout.log")
    stderr_path = os.path.join(_data_dir, "server.stderr.log")
    stdout_f = open(stdout_path, "w")
    stderr_f = open(stderr_path, "w")

    proc = subprocess.Popen(
        [sys.executable, "-m", "gamecompanion"],
        env=env,
        cwd=PROJECT_ROOT,
        stdout=stdout_f,
        stderr=stderr_f,
    )

    # Poll until the server accepts requests (up to 30 s)
    deadline = time.time() + 30
    while time.time() < deadline:
        # If the process already exited, surface the error immediately
        if proc.poll() is not None:
            stderr_f.flush()
            with open(stderr_path) as f:
                err_text = f.read()
            stdout_f.close()
            stderr_f.close()
            raise RuntimeError(
                f"Server process exited with code {proc.returncode}\n"
                f"stderr:\n{err_text}"
            )
        try:
            resp = httpx.get(BASE_URL, timeout=1.0, follow_redirects=True)
            if resp.status_code < 500:
                break
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
            pass
        time.sleep(0.5)
    else:
        proc.terminate()
        stdout_f.close()
        stderr_f.close()
        raise RuntimeError(f"Server did not become ready within 30 s at {BASE_URL}")

    yield BASE_URL

    # ── Teardown ──────────────────────────────────────────────────────────
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    stdout_f.close()
    stderr_f.close()


@pytest.fixture(autouse=True)
def reset_app(app_url):
    """Reset application state before every test.

    Calls POST /test/reset (only available when GAMECOMPANION_TEST_MODE=1),
    which wipes the database and config so each test starts from a
    "fresh install" state.
    """
    resp = httpx.post(f"{app_url}/test/reset", timeout=5.0)
    assert resp.status_code == 200, f"Reset failed: {resp.status_code} {resp.text}"
    yield
