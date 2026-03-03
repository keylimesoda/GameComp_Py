import json

from gamecompanion import llm


def test_format_api_error_authentication_message():
    msg = llm._format_api_error(Exception("API_KEY_INVALID: bad key"))
    assert "Authentication failed" in msg
    assert "<details>" in msg


def test_parse_llm_response_json_dict_and_fallback_plain_text():
    payload = json.dumps({"response": "ok", "context_deltas": [], "web_search": None})
    parsed = llm._parse_llm_response(payload)
    assert parsed["response"] == "ok"
    assert parsed["context_deltas"] == []

    parsed2 = llm._parse_llm_response("not json")
    assert parsed2["response"] == "not json"
    assert parsed2["context_deltas"] == []


def test_build_system_prompt_includes_game_and_playthrough():
    out = llm._build_system_prompt("Run A", "Elden Ring")
    assert "Run A" in out
    assert "Elden Ring" in out


def test_mock_llm_detects_character_and_returns_delta():
    raw = llm._mock_llm_respond("My character aria is a level 12 ranger with 18 dex")
    parsed = json.loads(raw)
    assert parsed["response"].lower().startswith("got it")
    assert parsed["context_deltas"]
    node = parsed["context_deltas"][0]
    assert node["name"] == "Aria"
    assert node["properties"]["level"] == 12
    assert node["properties"]["DEX"] == 18


def test_mock_llm_requests_web_search_for_strategy_questions():
    raw = llm._mock_llm_respond("How do I beat this boss?")
    parsed = json.loads(raw)
    assert parsed["web_search"] is not None
    assert "query" in parsed["web_search"]


def test_mock_llm_uses_search_results_when_available():
    raw = llm._mock_llm_respond("help", search_results="source docs")
    parsed = json.loads(raw)
    assert "Based on my research" in parsed["response"]
    assert "Sources:" in parsed["response"]
