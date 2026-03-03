import os
import importlib
import sqlite3

import pytest
import httpx


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("gamecompanion_data")
    os.environ["GAMECOMPANION_TEST_MODE"] = "1"
    os.environ["GAMECOMPANION_DATA_DIR"] = str(data_dir)
    os.environ["GAMECOMPANION_PORT"] = "0"

    # Patch fasthtml serve to avoid starting a real server at import time
    import fasthtml.common as fc
    fc.serve = lambda *args, **kwargs: None

    mod = importlib.import_module("gamecompanion.main")
    return mod


@pytest.fixture(scope="session")
def app(app_module):
    return app_module.app


@pytest.fixture(scope="session")
def data_dir(app_module):
    return app_module.DATA_DIR


@pytest.fixture(scope="session")
def db_path(app_module):
    return app_module.DB_PATH


@pytest.fixture()
async def async_client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
async def reset_app(async_client):
    resp = await async_client.post("/test/reset")
    assert resp.status_code == 200
    yield


def fetch_graph_nodes(db_path: str):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT name, kind, properties_json, status FROM graph_nodes").fetchall()
    con.close()
    return [dict(r) for r in rows]


def fetch_graph_node(db_path: str, name: str):
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT name, kind, properties_json, status FROM graph_nodes WHERE name = ?",
        (name,),
    ).fetchone()
    con.close()
    return dict(row) if row else None
