import re


async def test_root_shows_welcome_when_no_key(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert "data-testid=\"welcome-heading\"" in resp.text
    assert "data-testid=\"api-key-input\"" in resp.text
    assert "data-testid=\"save-key-btn\"" in resp.text


async def test_save_key_redirects_to_new_playthrough(async_client):
    resp = await async_client.post(
        "/setup/save-key",
        data={"api_key": "test-key-valid", "tavily_api_key": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers.get("location") == "/setup/new-playthrough"

    # Follow redirect and ensure create playthrough page shows
    resp2 = await async_client.get(resp.headers["location"])
    assert resp2.status_code == 200
    assert re.search(r"Create Your First Playthrough", resp2.text)
