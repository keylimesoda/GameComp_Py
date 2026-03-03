"""Fixtures for live E2E tests that hit the real Copilot endpoint."""

import os
import subprocess
import pytest


def _get_github_token() -> str:
    """Get GitHub token from env or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    pytest.skip("No GitHub token available (set GITHUB_TOKEN or install gh CLI)")


@pytest.fixture(scope="session")
def github_token() -> str:
    return _get_github_token()


@pytest.fixture(scope="session")
def llm_client(github_token):
    """Return an OpenAI client pointed at the Copilot endpoint."""
    from openai import OpenAI
    return OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=github_token,
    )
