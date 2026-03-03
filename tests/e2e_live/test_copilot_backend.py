"""Live E2E tests — hit real GitHub Copilot endpoint.

Run: GITHUB_TOKEN=$(gh auth token) python -m pytest tests/e2e_live/ -v
Or just: python -m pytest tests/e2e_live/ -v  (if gh CLI is authenticated)

These tests make real API calls and cost real tokens. They're slow (~2-5s each).
Mark with @pytest.mark.live so they can be excluded from CI.
"""

import json
import pytest

pytestmark = pytest.mark.live


class TestCopilotEndpoint:
    """Verify the Copilot endpoint is reachable and responds correctly."""

    def test_basic_completion(self, llm_client):
        """Smoke test: can we get any response at all?"""
        resp = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Reply with exactly: PONG"}],
            max_tokens=10,
        )
        assert resp.choices[0].message.content is not None
        assert len(resp.choices[0].message.content.strip()) > 0

    def test_system_prompt_respected(self, llm_client):
        """Verify system prompt is actually used."""
        resp = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a pirate. Always respond starting with 'Arr'."},
                {"role": "user", "content": "Hello!"},
            ],
            max_tokens=50,
        )
        text = resp.choices[0].message.content.strip()
        assert text.lower().startswith("arr"), f"Expected pirate response, got: {text}"


class TestLoreKeeperLLM:
    """Test LoreKeeper's actual LLM module against the live endpoint."""

    def test_call_llm_returns_text(self, github_token):
        """_call_llm (now Copilot-backed) returns a non-empty string."""
        from gamecompanion.llm import _call_llm, _build_system_prompt
        system = _build_system_prompt("TestRun", "Baldur's Gate 3")
        result = _call_llm(github_token, system, user_message="What class should I pick for my first playthrough?", model_name="gpt-4o")
        assert isinstance(result, str)
        assert len(result) > 20, f"Response too short: {result}"

    def test_structured_json_response(self, github_token):
        """Ask the LLM to return structured JSON and verify _parse_llm_response handles it."""
        from gamecompanion.llm import _call_llm, _parse_llm_response

        prompt = (
            "You MUST respond with ONLY valid JSON (no markdown, no code fences). "
            "Format: {\"response\": \"<your advice>\", \"context_deltas\": [], \"web_search\": null}\n\n"
            "User question: What's a good tank build in Baldur's Gate 3?"
        )
        raw = _call_llm(github_token, "You are a game advisor. Respond in JSON only.", user_message=prompt, model_name="gpt-4o")
        parsed = _parse_llm_response(raw)

        assert "response" in parsed
        assert isinstance(parsed["response"], str)
        assert len(parsed["response"]) > 10
        assert isinstance(parsed["context_deltas"], list)

    def test_context_delta_extraction(self, github_token):
        """Ask the LLM to generate context deltas and verify structure."""
        from gamecompanion.llm import _call_llm, _parse_llm_response

        prompt = (
            "You MUST respond with ONLY valid JSON (no markdown, no code fences).\n"
            "The user is telling you about their character. Extract the info into context_deltas.\n\n"
            "Format:\n"
            '{"response": "<acknowledge>", "context_deltas": [{"type": "graph", "operation": "upsert_node", '
            '"name": "<name>", "kind": "character", "properties": {"class": "...", "level": N}, '
            '"reason": "..."}], "web_search": null}\n\n'
            "User: My character Shadowheart is a level 5 Cleric."
        )
        raw = _call_llm(github_token, "You are LoreKeeper, a game companion AI.", user_message=prompt, model_name="gpt-4o")
        parsed = _parse_llm_response(raw)

        assert len(parsed["context_deltas"]) >= 1, f"Expected deltas, got: {parsed}"
        delta = parsed["context_deltas"][0]
        assert delta.get("name", "").lower() == "shadowheart"
        assert delta.get("kind") == "character"

    def test_validate_api_key_with_real_token(self, github_token):
        """_validate_api_key should pass with a real GitHub token."""
        import sys, os
        os.environ["GAMECOMPANION_TEST_MODE"] = ""  # Disable test mode for this
        sys.modules.pop("gamecompanion.main", None)  # Force reimport

        from gamecompanion.llm import _get_client, _DEFAULT_MODEL
        client = _get_client(github_token)
        resp = client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        assert resp.choices[0].message.content is not None


class TestModelAvailability:
    """Verify model listing works."""

    def test_available_models_returns_list(self):
        """In non-test mode, should return the known model list."""
        from gamecompanion.llm import _get_available_models
        models = _get_available_models("any-key")
        assert isinstance(models, list)
        assert "gpt-4o" in models

    def test_gpt4o_mini_available(self, llm_client):
        """Verify gpt-4o-mini works on the endpoint."""
        resp = llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
        )
        assert resp.choices[0].message.content is not None
