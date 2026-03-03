# LoreKeeper

AI-powered game companion with persistent, structured memory. Your AI remembers characters, relationships, quests, and world state across sessions — solving the context decay problem in long RPG campaigns.

See [spec.md](spec.md) for full product requirements.

## What It Does

LoreKeeper automatically builds and maintains structured knowledge (character sheets, relationship graphs, quest logs, world state) from your natural conversation with the AI. No manual note-taking — just play your game and talk about it.

Designed for games like Baldur's Gate 3, D&D campaigns, and any narrative-heavy RPG.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run
gamecompanion
```

Open http://localhost:8000 in your browser. You'll need a GitHub account for AI features (sign in via GitHub or paste a token).

## LLM Backend

LoreKeeper uses GitHub Copilot's API (OpenAI-compatible) — no separate API key needed. Just sign in with GitHub.

**Models available:** `gpt-4o` (default), `gpt-4o-mini` (faster), `o3-mini` (reasoning)

## Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Live E2E tests (hits real API)
GITHUB_TOKEN=$(gh auth token) pytest tests/e2e_live/ -v

# All tests
pytest
```

## Research Notes

- Repo status and near-term plan: [REPO_NOTES.md](REPO_NOTES.md)
- Test requirements: [test-spec.md](test-spec.md)
- Research protocol: [research-protocol.md](research-protocol.md)
