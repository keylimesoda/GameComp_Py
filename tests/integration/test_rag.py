import json


async def _create_playthrough(async_client, name="RAG Run"):
    resp = await async_client.post(
        "/playthrough/create",
        data={"name": name, "game_title": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    playthrough_id = int(resp.headers["location"].split("/")[-1])
    return playthrough_id


async def test_rag_retrieval_uses_older_messages(async_client):
    pid = await _create_playthrough(async_client)

    # Inject 11 messages so the first falls outside the recent-window exclusion
    messages = [
        {"role": "user", "content": "The dragon is weak to lightning damage."},
    ]
    for i in range(10):
        messages.append({"role": "user", "content": f"Filler message {i}"})

    resp = await async_client.post(
        f"/test/inject-messages?playthrough_id={pid}",
        data={"messages": json.dumps(messages)},
    )
    assert resp.status_code == 200

    resp2 = await async_client.get(f"/test/rag-stats?playthrough_id={pid}")
    assert resp2.status_code == 200
    assert resp2.json()["indexed_count"] >= len(messages)

    # Ask about the older message; mock LLM echoes RAG context
    resp3 = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Any tips on the dragon weakness?"},
    )
    assert resp3.status_code == 200
    assert "weak to lightning" in resp3.text
