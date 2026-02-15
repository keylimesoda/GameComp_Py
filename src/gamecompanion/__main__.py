"""Allow running with `python -m gamecompanion`."""

import os
import uvicorn

from gamecompanion.main import app

port = int(os.environ.get("GAMECOMPANION_PORT", "5001"))
uvicorn.run(app, host="127.0.0.1", port=port)
