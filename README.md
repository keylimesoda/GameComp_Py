# Game Companion

AI-powered game companion with persistent memory. See [spec.md](spec.md) for product requirements.

## Research Notes

- Repo status and near-term plan: [REPO_NOTES.md](REPO_NOTES.md)
- Test requirements: [test-spec.md](test-spec.md)
- Research protocol: [research-protocol.md](research-protocol.md)

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Install playwright browsers
playwright install chromium

# Run the app
gamecompanion
```

Then open http://localhost:8000 in your browser.

## Run Tests

```bash
# E2E tests (requires playwright)
pytest tests/e2e/

# All tests
pytest
```
