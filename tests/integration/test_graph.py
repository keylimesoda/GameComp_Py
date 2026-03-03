import json

from .conftest import fetch_graph_node


async def _create_playthrough(async_client, name="Graph Run", game_title=""):
    resp = await async_client.post(
        "/playthrough/create",
        data={"name": name, "game_title": game_title},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    playthrough_id = int(resp.headers["location"].split("/")[-1])
    return playthrough_id


async def test_graph_deltas_character_creation_and_updates(async_client, db_path):
    pid = await _create_playthrough(async_client)

    await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "My character Keth is a level 3 ranger with 16 dex"},
    )
    node = fetch_graph_node(db_path, "Keth")
    assert node is not None
    props = json.loads(node["properties_json"])
    assert props["class"] == "ranger"
    assert props["level"] == 3
    assert props["DEX"] == 16

    await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Leveled up Keth to level 4"},
    )
    node = fetch_graph_node(db_path, "Keth")
    props = json.loads(node["properties_json"])
    assert props["level"] == 4

    await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Keth has 14 WIS"},
    )
    node = fetch_graph_node(db_path, "Keth")
    props = json.loads(node["properties_json"])
    assert props["WIS"] == 14


async def test_memory_queries_character_sheet_and_party(async_client):
    pid = await _create_playthrough(async_client)

    await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Keth is a level 2 monk"},
    )
    await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Lia is a rogue in my party"},
    )

    resp = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "Show me Keth's character sheet"},
    )
    assert "Character Sheet - Keth" in resp.text
    assert "level 2" in resp.text

    resp2 = await async_client.post(
        f"/chat/{pid}/send",
        data={"message": "What do you remember about my party"},
    )
    assert "Party Summary:" in resp2.text
    assert "- Keth" in resp2.text
    assert "- Lia" in resp2.text
