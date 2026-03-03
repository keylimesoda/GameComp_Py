import re


async def _create_playthrough(async_client, name="Settings Run"):
    resp = await async_client.post(
        "/playthrough/create",
        data={"name": name, "game_title": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    return int(resp.headers["location"].split("/")[-1])


async def test_settings_save_and_load(async_client):
    # Ensure at least one playthrough exists for export select
    await _create_playthrough(async_client)

    resp = await async_client.post(
        "/settings/save",
        data={
            "gemini_api_key": "test-key-valid",
            "tavily_api_key": "tav-key",
            "debug_mode": "on",
            "model_name": "gemini-2.0-flash",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/settings?saved=1"

    resp2 = await async_client.get("/settings?saved=1")
    assert resp2.status_code == 200
    assert "Settings saved." in resp2.text
    assert "data-testid=\"gemini-key-status\"" in resp2.text
    assert re.search(r"gemini-2.0-flash", resp2.text)


async def test_test_key_endpoint(async_client):
    resp = await async_client.post("/api/test-key", data={"api_key": "test-key-valid"})
    assert resp.status_code == 200
    assert "data-testid=\"api-key-status\"" in resp.text
    assert "✓" in resp.text
