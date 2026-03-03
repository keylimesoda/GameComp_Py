import re


async def _create_playthrough(async_client, name="Test Run", game_title="Baldur's Gate 3"):
    resp = await async_client.post(
        "/playthrough/create",
        data={"name": name, "game_title": game_title},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/chat/")
    playthrough_id = int(location.split("/")[-1])
    return playthrough_id, location


async def test_create_playthrough_shows_welcome_message(async_client):
    pid, location = await _create_playthrough(async_client)
    resp = await async_client.get(location)
    assert resp.status_code == 200
    assert "data-testid=\"ai-message\"" in resp.text
    assert "your game companion" in resp.text.lower()


async def test_send_message_returns_ai_response(async_client):
    pid, _ = await _create_playthrough(async_client, game_title="")
    resp = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Any tips for a stealth build?"},
    )
    assert resp.status_code == 200
    assert "data-testid=\"user-message\"" in resp.text
    assert "data-testid=\"ai-message\"" in resp.text
    assert "Gloom Stalker" in resp.text


async def test_web_search_flow_uses_mock_results(async_client):
    pid, _ = await _create_playthrough(async_client)
    resp = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "How do I beat the dragon boss?"},
    )
    assert resp.status_code == 200
    assert "Sources:" in resp.text
    assert "https://www.gamesguide.com/strategy" in resp.text
    assert "https://wiki.gameinfo.com/guide" in resp.text
    assert re.search(r"\[1\].*gamesguide", resp.text)


async def test_offline_mode_returns_warning(async_client):
    pid, _ = await _create_playthrough(async_client)
    await async_client.post(
        "/test/set-config",
        json={"force_offline": True},
    )
    resp = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Hello?"},
    )
    assert resp.status_code == 200
    assert "You’re offline" in resp.text or "You're offline" in resp.text


async def test_api_error_formats_message(async_client):
    pid, _ = await _create_playthrough(async_client)
    await async_client.post(
        "/test/set-config",
        json={"force_api_error": "API_KEY_INVALID"},
    )
    resp = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Hello?"},
    )
    assert resp.status_code == 200
    assert "Authentication failed" in resp.text
