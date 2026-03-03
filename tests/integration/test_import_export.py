import io
import json
import zipfile


async def _create_playthrough(async_client, name="Export Run", game_title=""):
    resp = await async_client.post(
        "/playthrough/create",
        data={"name": name, "game_title": game_title},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    return int(resp.headers["location"].split("/")[-1])


async def test_export_and_import_playthrough(async_client):
    pid = await _create_playthrough(async_client, name="Export Me")

    # Create some stable context
    await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Keth is a level 2 monk"},
    )

    export_resp = await async_client.get(f"/playthrough/export?playthrough_id={pid}")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(export_resp.content))
    assert set(zf.namelist()) == {"playthrough.json", "messages.json", "stable_context.json"}
    stable_context = json.loads(zf.read("stable_context.json"))
    assert any(n.get("name") == "Keth" for n in stable_context.get("nodes", []))

    # Import into a new playthrough
    files = {"import_file": ("playthrough.zip", export_resp.content, "application/zip")}
    import_resp = await async_client.post("/playthrough/import", files=files, follow_redirects=False)
    assert import_resp.status_code == 303
    new_location = import_resp.headers["location"]
    assert new_location.startswith("/chat/")

    chat_resp = await async_client.get(new_location)
    assert chat_resp.status_code == 200
    assert "Export Me" in chat_resp.text


async def test_rename_and_delete_playthrough(async_client):
    pid1 = await _create_playthrough(async_client, name="First Run")
    pid2 = await _create_playthrough(async_client, name="Second Run")

    rename_resp = await async_client.post(
        f"/playthrough/{pid1}/rename",
        data={"name": "Renamed Run", "game_title": ""},
        follow_redirects=False,
    )
    assert rename_resp.status_code == 303
    assert rename_resp.headers["location"] == f"/chat/{pid1}"

    chat_resp = await async_client.get(f"/chat/{pid1}")
    assert "Renamed Run" in chat_resp.text

    delete_resp = await async_client.get(f"/playthrough/{pid1}/delete", follow_redirects=False)
    assert delete_resp.status_code == 303
    assert delete_resp.headers["location"] == f"/chat/{pid2}"
