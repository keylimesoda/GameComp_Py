"""LLM helpers — GitHub Copilot (OpenAI-compatible) backend."""

import json
import os
import re
import time

from openai import OpenAI


# ── Constants ────────────────────────────────────────────────────────────────

_COPILOT_ENDPOINT = "https://models.inference.ai.azure.com"

_SYSTEM_PROMPT = """\
You are LoreKeeper, a knowledgeable and friendly AI co-pilot for video game \
playthroughs. You remember everything the player tells you about their game, \
characters, decisions, and progress. You give helpful advice on builds, strategy, \
lore, and roleplay. Keep answers concise but thorough. If the player has told you \
about their character or party, reference that context naturally."""

_SEARCH_TRIGGER_KEYWORDS = [
    "beat", "defeat", "boss", "weapon", "armor", "item",
    "strategy", "guide", "tips", "build", "enemy", "enemies",
    "immune", "resist", "weakness", "location", "where to find",
    "how to get", "how do i", "quest", "npc", "spell", "ability",
    "class", "subclass", "feat", "skill", "level", "stats",
    "damage", "best", "optimal", "recommend", "counter",
    "wiki", "patch", "nerf", "buff", "meta",
]

_MOCK_SEARCH_RESULTS = [
    {
        "title": "Game Strategy Guide",
        "url": "https://www.gamesguide.com/strategy",
        "content": "Detailed strategy and tips for defeating difficult bosses and challenges.",
    },
    {
        "title": "Wiki Game Guide",
        "url": "https://wiki.gameinfo.com/guide",
        "content": "Comprehensive game information including builds, items, and boss strategies.",
    },
]

# ── Default model ────────────────────────────────────────────────────────────

_DEFAULT_MODEL = "gpt-4o"

# ── Available models on GitHub Copilot endpoint ──────────────────────────────

_COPILOT_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "o3-mini",
]


# ── Client factory ───────────────────────────────────────────────────────────

def _get_client(api_key: str) -> OpenAI:
    """Return an OpenAI client pointed at the Copilot inference endpoint."""
    return OpenAI(
        base_url=_COPILOT_ENDPOINT,
        api_key=api_key,
    )


# ── Public helpers ───────────────────────────────────────────────────────────

def _format_api_error(exc: Exception) -> str:
    raw = str(exc)
    lower = raw.lower()
    if "api_key_invalid" in lower or "401" in lower or "invalid api key" in lower:
        friendly = "Authentication failed. Check your API key."
    elif "429" in lower or "resource_exhausted" in lower or "rate limit" in lower or "rate_limit" in lower:
        friendly = "Rate limit reached. Please wait and try again."
    elif "timeout" in lower or "timed out" in lower or "connection" in lower:
        friendly = "Network error. Check your connection."
    else:
        friendly = "API error. Please try again."
    details = (
        "\n\n<details><summary>Details</summary>\n\n"
        + "```\n"
        + raw
        + "\n```\n\n</details>"
    )
    return f"⚠️ {friendly}{details}"


def _get_available_models(api_key: str, test_mode: bool = False) -> list[str]:
    """Return models available on the Copilot endpoint."""
    if test_mode:
        return list(_COPILOT_MODELS)
    if not api_key:
        return []
    # The Copilot endpoint doesn't have a list-models API,
    # so return the known set. Could probe with a tiny request if needed.
    return list(_COPILOT_MODELS)


def _build_system_prompt(playthrough_name: str, game_title: str) -> str:
    parts = [_SYSTEM_PROMPT]
    if game_title:
        parts.append(f"\nThe player is currently playing: {game_title}.")
    if playthrough_name:
        parts.append(f"\nPlaythrough name: {playthrough_name}.")
    return "\n".join(parts)


def _call_llm(api_key: str, system_prompt: str, history: list[dict] | None = None,
              user_message: str = "", *, model_name: str = "") -> str:
    """Call the LLM via the Copilot endpoint."""
    client = _get_client(api_key)
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    if user_message:
        messages.append({"role": "user", "content": user_message})
    resp = client.chat.completions.create(
        model=model_name or _DEFAULT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    return resp.choices[0].message.content or ""


def _parse_llm_response(raw_text: str) -> dict:
    try:
        parsed = json.loads(raw_text)
    except Exception:
        return {
            "response": raw_text.strip() if raw_text else "",
            "context_deltas": [],
            "web_search": None,
        }

    if not isinstance(parsed, dict):
        return {"response": str(parsed), "context_deltas": [], "web_search": None}

    return {
        "response": parsed.get("response", "") if isinstance(parsed.get("response", ""), str) else str(parsed.get("response", "")),
        "context_deltas": parsed.get("context_deltas", []) if isinstance(parsed.get("context_deltas", []), list) else [],
        "web_search": parsed.get("web_search", None),
    }


def _mock_llm_respond(
    user_message: str,
    rag_context: str = "",
    search_results: str = "",
    stable_context: dict | None = None,
) -> str:
    """Mock LLM for test mode — no network calls."""
    time.sleep(0.8)
    stable_context = stable_context or {}
    lower = user_message.lower()

    if search_results:
        return json.dumps({
            "response": (
                "Based on my research, here are some helpful tips:\n\n"
                "You should focus on learning attack patterns and timing your "
                "dodges carefully. Using spirit summons can help draw aggro "
                "while you deal damage [1]. There are also special items that "
                "can give you an advantage in this fight [2].\n\n"
                "Sources:\n"
                "[1] https://www.gamesguide.com/strategy\n"
                "[2] https://wiki.gameinfo.com/guide"
            ),
            "context_deltas": [],
            "web_search": None,
        })

    if rag_context:
        return json.dumps({"response": rag_context, "context_deltas": [], "web_search": None})

    deltas: list[dict] = []
    match = re.search(r"my character (\w+) is a level (\d+) ([\w\s-]+?) with (\d+) dex", lower)
    if match:
        deltas.append({
            "type": "graph",
            "operation": "upsert_node",
            "name": match.group(1).capitalize(),
            "kind": "character",
            "properties": {
                "role": "protagonist",
                "class": match.group(3).strip(),
                "level": int(match.group(2)),
                "DEX": int(match.group(4)),
            },
            "reason": "User provided character details",
        })

    needs_search = any(kw in lower for kw in _SEARCH_TRIGGER_KEYWORDS)
    if needs_search and not deltas:
        return json.dumps({
            "response": "I'll look that up for you.",
            "context_deltas": [],
            "web_search": {
                "query": user_message,
                "reason": "Game-specific question requiring current information",
            },
        })

    if deltas:
        return json.dumps({"response": "Got it — I'll remember that.", "context_deltas": deltas, "web_search": None})

    return json.dumps({
        "response": "Great question! For a sneaky character, I'd recommend a Gloom Stalker Ranger or a Shadow Monk.",
        "context_deltas": [],
        "web_search": None,
    })
