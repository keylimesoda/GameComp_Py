"""LoreKeeper – FastHTML Application.

This is the main entry point.  Run with:
    python -m gamecompanion.main

Environment variables (all optional):
    GAMECOMPANION_PORT       – HTTP port (default 5001)
    GAMECOMPANION_DATA_DIR   – directory for SQLite DB & config (default ./data)
    GAMECOMPANION_TEST_MODE  – set to "1" to enable mock LLM & /test/reset
"""

from __future__ import annotations

import os
import json
import sqlite3
import traceback
import math
import re
import io
import zipfile
import urllib.request
from datetime import datetime
from collections import Counter
from pathlib import Path

from openai import OpenAI
from .config import DATA_DIR, DB_PATH, CONFIG_PATH, TEST_MODE
PORT = int(os.environ.get("GAMECOMPANION_PORT", "5001"))
from .db import ensure_tables as _ensure_tables, get_db as _get_db
from .llm import (
    _format_api_error, _get_available_models, _SYSTEM_PROMPT,
    _build_system_prompt, _SEARCH_TRIGGER_KEYWORDS, _MOCK_SEARCH_RESULTS,
    _mock_llm_respond, _call_llm, _parse_llm_response,
)
from .rag import (
    _tokenize, _vectorize, _cosine_sim,
    _rag_index_message, _rag_recent_message_ids, _build_rag_context,
)
from .graph import (
    _get_node, _upsert_node, _get_nodes_by_kind, _get_all_nodes,
    _get_all_edges, _add_edge, _remove_edge, _remove_node,
    _update_json_path, _add_json_path,
)
from .memory import _load_stable_context

from fasthtml.common import *
from starlette.responses import JSONResponse, StreamingResponse
from starlette.requests import Request
from starlette.datastructures import UploadFile
import markdown as _md

# ── Configuration ─────────────────────────────────────────────────────────


# ── Database helpers ──────────────────────────────────────────────────────


# ── Config helpers ────────────────────────────────────────────────────────


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def _save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg))


def _is_offline(cfg: dict) -> bool:
    if TEST_MODE and cfg.get("force_offline"):
        return True
    if TEST_MODE:
        return False
    try:
        urllib.request.urlopen("https://www.google.com/generate_204", timeout=2)
        return False
    except Exception:
        return True






# ── LLM helpers ───────────────────────────────────────────────────────────





# Keywords that signal a game-specific query needing web search (used by mock LLM)

# Canned search results used by the mock Tavily in test mode




# ── RAG helpers ───────────────────────────────────────────────────────────

_STOPWORDS = {
    "the", "and", "or", "to", "a", "an", "of", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "being", "it", "that", "this",
    "as", "at", "by", "from", "about", "into", "my", "your", "our", "their",
    "i", "you", "we", "they", "he", "she", "them", "me", "us", "his", "her",
    "what", "which", "who", "whom", "when", "where", "why", "how",
}

RECENT_WINDOW_SIZE = 10
RAG_TOP_K = 3












def _rag_search(
    db: sqlite3.Connection,
    playthrough_id: int,
    query: str,
    exclude_message_ids: set[int] | None = None,
) -> list[str]:
    exclude_message_ids = exclude_message_ids or set()
    q_vec = _vectorize(query)
    if not q_vec:
        return []
    rows = db.execute(
        "SELECT message_id, content, tokens_json FROM rag_chunks WHERE playthrough_id = ?",
        (playthrough_id,),
    ).fetchall()
    scored: list[tuple[float, str]] = []
    for r in rows:
        if r["message_id"] in exclude_message_ids:
            continue
        tokens = Counter(json.loads(r["tokens_json"]))
        score = _cosine_sim(q_vec, tokens)
        if score > 0.05:
            scored.append((score, r["content"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:RAG_TOP_K]]




def _validate_api_key(key: str) -> tuple[bool, str]:
    """Validate the API key against the GitHub Copilot endpoint.

    Returns (is_valid, message).
    In test mode, 'test-key-valid' always passes.
    """
    if TEST_MODE:
        if key == "test-key-valid":
            return True, "Key is valid"
        return False, "Key is invalid"
    if not key or len(key.strip()) < 10:
        return False, "Key is too short"
    try:
        from .llm import _get_client, _DEFAULT_MODEL
        client = _get_client(key)
        # Light-weight validation: tiny completion
        resp = client.chat.completions.create(
            model=_DEFAULT_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        return True, "Valid — connected to GitHub Copilot endpoint"
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "auth" in msg.lower():
            return False, "Invalid API key — check your GitHub token"
        return False, f"Validation failed: {msg[:120]}"




# ── Markdown rendering ────────────────────────────────────────────────────

def _render_ai_message(content: str) -> NotStr:
    """Convert markdown AI response to HTML for display."""
    html = _md.markdown(content, extensions=["fenced_code", "tables", "nl2br"])
    return NotStr(html)


# ── Knowledge graph helpers (stable context) ─────────────────────────────


















# ── Stable context load / format (graph-backed) ─────────────────────────




def _stable_context_to_text(ctx: dict) -> str:
    """Serialize the knowledge graph for inclusion in the LLM system prompt."""
    return (
        "CURRENT KNOWLEDGE GRAPH (this is what you have saved — review it and "
        "emit context_deltas for ANYTHING the conversation implies that is "
        "missing or outdated):\n"
        + json.dumps(ctx, ensure_ascii=False, indent=2)
    )


def _summarize_stable_context(ctx: dict) -> str:
    """Return a short, user-friendly summary of the knowledge graph."""
    nodes = ctx.get("nodes", []) or []
    edges = ctx.get("edges", []) or []

    parts: list[str] = []
    characters = [n for n in nodes if n.get("kind") == "character"]
    if characters:
        names = ", ".join(n.get("name", "?") for n in characters[:5])
        extra = f" (+{len(characters) - 5} more)" if len(characters) > 5 else ""
        parts.append(f"Entities: {names}{extra}")

    world = next((n for n in nodes if n.get("kind") == "world"), None)
    if world:
        props = world.get("properties", {})
        prog = props.get("progression", "")
        loc = props.get("location", "")
        if prog and loc:
            parts.append(f"World: {prog}, {loc}")
        elif prog:
            parts.append(f"World: {prog}")
        elif loc:
            parts.append(f"World: {loc}")

    decisions = [n for n in nodes if n.get("kind") == "decision"]
    if decisions:
        parts.append(f"Decisions: {len(decisions)}")

    codex = next((n for n in nodes if n.get("kind") == "codex"), None)
    if codex:
        hr = codex.get("properties", {}).get("houseRules", [])
        if hr:
            parts.append(f"House rules: {len(hr)}")

    narrative = next((n for n in nodes if n.get("kind") == "narrative"), None)
    if narrative:
        threads = narrative.get("properties", {}).get("threads", [])
        if threads:
            parts.append(f"Narrative: {len(threads)} note(s)")

    if edges:
        parts.append(f"Relationships: {len(edges)}")

    return "; ".join(parts) if parts else "No stable context saved yet."






def _apply_context_deltas(
    db: sqlite3.Connection,
    playthrough_id: int,
    deltas: list[dict],
) -> int:
    """Apply graph context deltas. Returns number of deltas applied."""
    applied = 0
    for d in deltas or []:
        op = d.get("operation")

        if op == "upsert_node":
            name = d.get("name")
            kind = d.get("kind")
            if not name or not kind:
                continue
            existing = _get_node(db, playthrough_id, name)
            if existing:
                # Merge new properties into existing
                merged = existing["properties"].copy()
                merged.update(d.get("properties") or {})
                _upsert_node(db, playthrough_id, name, kind, merged,
                             d.get("status", existing.get("status", "active")))
            else:
                _upsert_node(db, playthrough_id, name, kind,
                             d.get("properties") or {},
                             d.get("status", "active"))
            applied += 1

        elif op == "update_property":
            name = d.get("name")
            prop = d.get("property")
            if not name or not prop:
                continue
            node = _get_node(db, playthrough_id, name)
            if not node:
                # Auto-create node (matches old default-entity-sheet behavior)
                kind = "narrative" if name == "__narrative__" else \
                       "codex" if name == "__codex__" else \
                       "world" if name == "__world__" else "character"
                _upsert_node(db, playthrough_id, name, kind, {})
                node = _get_node(db, playthrough_id, name)
            props = node["properties"]
            _update_json_path(props, prop, d.get("value"))
            _upsert_node(db, playthrough_id, name, node["kind"], props)
            applied += 1

        elif op == "add_to_list":
            name = d.get("name")
            prop = d.get("property")
            if not name or not prop:
                continue
            node = _get_node(db, playthrough_id, name)
            if not node:
                # Auto-create node for well-known singletons
                kind = "narrative" if name == "__narrative__" else \
                       "codex" if name == "__codex__" else \
                       "world" if name == "__world__" else "misc"
                _upsert_node(db, playthrough_id, name, kind, {})
                node = _get_node(db, playthrough_id, name)
            props = node["properties"]
            _add_json_path(props, prop, d.get("value"))
            _upsert_node(db, playthrough_id, name, node["kind"], props)
            applied += 1

        elif op == "add_edge":
            src = d.get("source")
            tgt = d.get("target")
            label = d.get("label")
            if src and tgt and label:
                _add_edge(db, playthrough_id, src, tgt, label,
                          d.get("properties"))
                applied += 1

        elif op == "remove_edge":
            src = d.get("source")
            tgt = d.get("target")
            label = d.get("label")
            if src and tgt and label:
                _remove_edge(db, playthrough_id, src, tgt, label)
                applied += 1

        elif op == "remove_node":
            name = d.get("name")
            if name:
                _remove_node(db, playthrough_id, name)
                applied += 1

    return applied


def _append_changelog(playthrough_id: int, deltas: list[dict]):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "playthrough_id": playthrough_id,
        "deltas": deltas,
    }
    path = DATA_DIR / "changelog.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _summarize_context_deltas(deltas: list[dict]) -> tuple[str, str]:
    """Return (short_summary, details_markdown) for applied graph deltas."""
    if not deltas:
        return "", ""
    short_bits: list[str] = []
    detail_lines: list[str] = []
    for d in deltas:
        op = d.get("operation")
        name = d.get("name", "")
        prop = d.get("property", "")
        value = d.get("value")
        reason = d.get("reason")

        if op == "upsert_node":
            kind = d.get("kind", "")
            short_bits.append(f"Added {name}")
            detail_lines.append(f"- Added {kind} node: {name}")
        elif op == "update_property" and name:
            short_bits.append(f"Updated {name}")
            detail_lines.append(f"- Updated {name}.{prop} = {value}")
        elif op == "add_to_list" and name:
            display = name if not name.startswith("__") else name.strip("_")
            short_bits.append(f"Updated {display}")
            detail_lines.append(f"- Added to {display}.{prop}: {value}")
        elif op == "add_edge":
            src = d.get("source", "")
            tgt = d.get("target", "")
            label = d.get("label", "")
            short_bits.append(f"Linked {src} → {tgt}")
            detail_lines.append(f"- Edge: {src} —[{label}]→ {tgt}")
        elif op == "remove_edge":
            src = d.get("source", "")
            tgt = d.get("target", "")
            short_bits.append(f"Unlinked {src} ↛ {tgt}")
            detail_lines.append(f"- Removed edge: {src} → {tgt}")
        elif op == "remove_node" and name:
            short_bits.append(f"Removed {name}")
            detail_lines.append(f"- Removed node: {name}")

        if reason:
            detail_lines.append(f"  ↳ {reason}")

    short_summary = ", ".join(dict.fromkeys(short_bits)) if short_bits else "Memory updated"
    details_md = "\n".join(detail_lines)
    return short_summary, details_md


def _format_character_node(node: dict) -> str:
    """Format a character-type graph node for display."""
    name = node.get("name", "Unknown")
    props = node.get("properties", {})
    lines = [f"Character Sheet - {name}"]
    if props.get("role"):
        lines.append(f"Role: {props['role']}")
    if props.get("class"):
        lines.append(f"Class: {props['class']}")
    if "level" in props:
        lines.append(f"level {props['level']}")
    for stat in ["DEX", "WIS", "STR", "CON", "INT", "CHA"]:
        if stat in props:
            lines.append(f"{stat} {props[stat]}")
    if props.get("notes"):
        lines.append(f"Notes: {props['notes']}")
    return "\n".join(lines)


def _format_party_summary(characters: list[dict]) -> str:
    """Format a summary of all character nodes."""
    if not characters:
        return "I don't have any party members saved yet."
    lines = ["Party Summary:"]
    for n in characters:
        name = n.get("name", "Unknown")
        props = n.get("properties", {})
        detail = []
        if props.get("class"):
            detail.append(props["class"])
        if "level" in props:
            detail.append(f"level {props['level']}")
        if "DEX" in props:
            detail.append(f"DEX {props['DEX']}")
        suffix = " — " + ", ".join(detail) if detail else ""
        lines.append(f"- {name}{suffix}")
    return "\n".join(lines)


def _format_world_state(world_node: dict | None) -> str:
    """Format the world-state graph node for display."""
    if not world_node:
        return "I don't have a world state saved yet."
    props = world_node.get("properties", {})
    parts = []
    if props.get("progression"):
        parts.append(f"Progression: {props['progression']}")
    if props.get("location"):
        parts.append(f"Location: {props['location']}")
    if props.get("activeGoals"):
        parts.append(f"Active Goals: {', '.join(props['activeGoals'])}")
    if not parts:
        return "I don't have a world state saved yet."
    return "\n".join(parts)


def _maybe_handle_memory_query(message: str, ctx: dict) -> str | None:
    """Handle natural-language memory queries against the knowledge graph."""
    text = message.strip()
    lower = text.lower()
    nodes = ctx.get("nodes", [])

    # ── Show full graph ───────────────────────────────────────────────
    if (
        "share what stable context" in lower
        or "share stable context" in lower
        or "show stable context" in lower
        or "show me stable context" in lower
        or "show all stable context" in lower
        or "show me all stable context" in lower
        or "show me all the stable context" in lower
        or "show all the stable context" in lower
        or "show knowledge graph" in lower
        or "show me the knowledge graph" in lower
    ):
        summary = _summarize_stable_context(ctx)
        details = (
            "\n\n<details><summary>View full knowledge graph</summary>\n\n"
            + "```json\n"
            + json.dumps(ctx, ensure_ascii=False, indent=2)
            + "\n```\n\n</details>"
        )
        return f"Knowledge graph summary: {summary}{details}"

    # ── Character sheet ───────────────────────────────────────────────
    match = re.search(r"show me (.+?)'s character sheet", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        node = next((n for n in nodes if n["name"].lower() == name.lower()
                      and n.get("kind") == "character"), None)
        if node:
            return _format_character_node(node)
        return f"I don't have a character sheet for {name} yet."

    match = re.search(r"show me (.+?)'s stats", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        node = next((n for n in nodes if n["name"].lower() == name.lower()
                      and n.get("kind") == "character"), None)
        if node:
            return _format_character_node(node)
        return f"I don't have stats for {name} yet."

    # ── Party summary ─────────────────────────────────────────────────
    if "what do you remember about my party" in lower:
        characters = [n for n in nodes if n.get("kind") == "character"]
        return _format_party_summary(characters)

    # ── World state ───────────────────────────────────────────────────
    if "where am i in the story" in lower:
        world = next((n for n in nodes if n.get("kind") == "world"), None)
        return _format_world_state(world)

    # ── House rules ───────────────────────────────────────────────────
    if "what are my house rules" in lower:
        codex = next((n for n in nodes if n.get("kind") == "codex"), None)
        house_rules = codex.get("properties", {}).get("houseRules", []) if codex else []
        if not house_rules:
            return "I don't have any house rules saved yet."
        return "House Rules:\n" + "\n".join(f"- {r}" for r in house_rules)

    # ── What do you remember about X? ─────────────────────────────────
    match = re.search(r"what do you remember about (.+?)\?*$", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        node = next((n for n in nodes if n["name"].lower() == name.lower()), None)
        if node:
            return _format_character_node(node)
        # Check narrative threads for mentions
        narrative = next((n for n in nodes if n.get("kind") == "narrative"), None)
        if narrative:
            threads = narrative.get("properties", {}).get("threads", [])
            matching = [t for t in threads if name.lower() in t.lower()]
            if matching:
                return "\n".join(matching)
        return None

    return None


# ── Structured output parsing ─────────────────────────────────────────


def _strip_json_blobs(text: str) -> str:
    """Remove large JSON objects accidentally leaked into AI response text.

    LLM sometimes dumps the full knowledge-graph JSON inside its
    conversational reply.  We detect top-level { … } blocks that look
    like structured data and strip them.
    """
    _CONTEXT_KEYS = {"nodes", "edges", "properties", "kind"}
    result = text
    brace_positions = [i for i, ch in enumerate(text) if ch == '{']
    # Walk biggest blocks first so indices stay valid after removal
    removals: list[tuple[int, int]] = []
    for start in brace_positions:
        depth = 0
        end = None
        for j in range(start, len(text)):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None:
            continue
        candidate = text[start:end + 1]
        # Only strip if it's ≥ 100 chars and looks like stable context or entity data
        if len(candidate) >= 100:
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict) and _CONTEXT_KEYS & set(obj.keys()):
                    removals.append((start, end + 1))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
    # Apply removals from back to front to preserve indices
    for s, e in reversed(removals):
        result = result[:s] + result[e:]
    # Clean up leftover whitespace
    result = re.sub(r'\n{3,}', '\n\n', result).strip()
    return result




# ── Web search helpers ────────────────────────────────────────────────────


def _mock_tavily_search(query: str) -> list[dict]:
    """Return canned search results for test mode."""
    return _MOCK_SEARCH_RESULTS


def _call_tavily_search(
    api_key: str, query: str, max_results: int = 5
) -> list[dict] | None:
    """Call the Tavily API for web search. Returns list of results or None on failure."""
    try:
        from tavily import TavilyClient  # lazy import — optional dep
    except ImportError:
        print("[Warning] tavily-python not installed. Web search unavailable.")
        return None
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=max_results)
        return response.get("results", [])
    except Exception as exc:
        print(f"[Tavily] Search failed: {exc}")
        return None


def _format_search_results(results: list[dict]) -> str:
    """Format search results for inclusion in the LLM prompt."""
    parts = ["Web search results:"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")[:500]
        parts.append(f"[{i}] {title} ({url})")
        parts.append(f"    {content}")
    return "\n".join(parts)


_STRUCTURED_OUTPUT_INSTRUCTIONS = """

CRITICAL RESPONSE FORMAT — you MUST follow these rules:

1. Your ENTIRE response must be a single valid JSON object. No text before or after it.
2. The JSON format is:
    {"response": "your reply here", "context_deltas": [], "web_search": null}

3. context_deltas: YOU ARE RESPONSIBLE for keeping the knowledge graph ACCURATE and
   UP-TO-DATE at all times. The knowledge graph stores everything as NODES (entities,
   concepts, game state) connected by EDGES (relationships). Emit deltas whenever
   game state has changed, including:
   • The user explicitly states new info ("My character Gale is a Warlock").
   • The user confirms they took an action ("Done", "I did it", "Okay I took that level",
     "I did exactly as you suggested"). In this case, derive what changed from YOUR
     OWN prior suggestion in the conversation history and emit deltas for it.
   • You gave build/level/ability advice AND the user accepted or confirmed it —
     emit deltas for every change implied (level, new abilities, new spells, etc.).
   • The user corrects a fact ("Actually his WIS is 18, not 16").
   • The user pins a fact ("Remember this: ...").
   • Any other information that updates a character, party, world state, or rules.
   If truly nothing changed, use [].

   IMPORTANT: Compare the CURRENT knowledge graph (provided below) with the
   conversation. If the conversation implies changes that the graph does NOT
   yet reflect, you MUST emit corrective deltas. Never leave the graph stale.

   ANY type of node can be created dynamically. Use descriptive kinds: character,
   location, item, faction, quest, world, codex, narrative, decision, vehicle,
   base, team, or anything else that fits the game.

   Delta schema (follow exactly):

   - Create/update a node:
       {"type": "graph", "operation": "upsert_node", "name": "Gale",
        "kind": "character",
        "properties": {"role": "companion", "class": "Warlock", "level": 1,
                       "notes": "Leftover pact from Mystra"},
        "reason": "User chose starting class and backstory"}

   - Update a single property on an existing node:
       {"type": "graph", "operation": "update_property", "name": "Gale",
        "property": "level", "value": 2,
        "reason": "User confirmed they leveled up"}

   - Add a value to a list property:
       {"type": "graph", "operation": "add_to_list", "name": "Gale",
        "property": "abilities", "value": "Agonizing Blast",
        "reason": "User confirmed taking Eldritch Invocation"}

   - Create a relationship between nodes:
       {"type": "graph", "operation": "add_edge",
        "source": "Gale", "target": "Party", "label": "member_of",
        "reason": "User added Gale to party"}

   - Remove a relationship:
       {"type": "graph", "operation": "remove_edge",
        "source": "Gale", "target": "Party", "label": "member_of",
        "reason": "Gale left the party"}

   - Remove a node entirely:
       {"type": "graph", "operation": "remove_node", "name": "OldNPC",
        "reason": "No longer relevant"}

   Well-known singleton nodes (auto-created if needed):
   • "__world__" (kind: "world") — progression, location, activeGoals, etc.
   • "__codex__" (kind: "codex") — houseRules, difficulty, mods, preferences
   • "__narrative__" (kind: "narrative") — threads (list of pinned story notes)

   Examples:

   Player codex (house rule):
       {"type": "graph", "operation": "add_to_list", "name": "__codex__",
        "property": "houseRules", "value": "Non-lethal approach whenever possible",
        "reason": "User stated a house rule"}

   Pinned fact:
       {"type": "graph", "operation": "add_to_list", "name": "__narrative__",
        "property": "threads",
        "value": "Leftover pact from Mystra for Gale",
        "reason": "User pinned backstory"}

   World state:
       {"type": "graph", "operation": "upsert_node", "name": "__world__",
        "kind": "world",
        "properties": {"progression": "Act 2", "location": "Moonrise Towers"},
        "reason": "User reported progression"}

   Example flow: User says "Done. I did exactly as you suggested." after you
   advised taking Warlock level 2 with Agonizing Blast and Devil's Sight:
     {"type":"graph","operation":"update_property","name":"Gale",
      "property":"level","value":2,"reason":"User confirmed level-up to 2"}
     {"type":"graph","operation":"add_to_list","name":"Gale",
      "property":"abilities","value":"Agonizing Blast","reason":"User confirmed invocation"}
     {"type":"graph","operation":"add_to_list","name":"Gale",
      "property":"abilities","value":"Devil's Sight","reason":"User confirmed invocation"}

4. For ANY question about specific game facts, mechanics, stats, enemies, items,
    bosses, builds, strategies, locations, NPCs, quests, spells, abilities, or
    patch/balance information — you MUST set web_search to trigger a search:
    {"response": "brief acknowledgment", "context_deltas": [],
     "web_search": {"query": "specific search terms", "reason": "why"}}

5. NEVER suggest the user search manually. NEVER say "I recommend a web search" or
    "you should look that up". If information would benefit from a search, USE the
    web_search field — that is what it is for. You have web search capability.

6. Only set web_search to null for: greetings, opinion questions, recall of prior
    conversation, roleplay/storytelling, or topics you are fully confident about
    from the conversation context alone.

7. If the user explicitly asks to record, update, or add details to a character sheet,
   you MUST include context_deltas for those details.

8. NEVER repeat or echo the user's message back as your own response.

9. The "response" field must contain ONLY natural conversational text. NEVER put
   raw JSON, the knowledge graph, node data, or any data structure inside the
   "response" value. If the user asks you to update context, just confirm in
   plain English (e.g. "Done, I've updated Gale's spells.") and put the actual
   changes in context_deltas. NEVER echo back the knowledge graph.

10. Output ONLY the JSON object. No markdown fences, no preamble, no extra text."""

_SEARCH_CITATION_INSTRUCTIONS = """

Web search results are provided below. Use them to give accurate, specific advice.
Include source URLs as numbered citations [1], [2], etc. in your response text.
At the end of your response, list the sources with their URLs.

Respond with the same JSON format:
{"response": "your reply with citations [1] [2]...", "context_deltas": [], "web_search": null}
Set web_search to null since search was already performed. Only include context_deltas
for updates implied by the USER'S message.
"""


# ── App factory ───────────────────────────────────────────────────────────

_ensure_tables(DB_PATH)

app, rt = fast_app(
    pico=True,
    htmlkw={"data-theme": "dark"},
    hdrs=(
        Style(
            """
            :root { --pico-background-color: #13171f; }
            body { min-height: 100vh; }
            html::-webkit-scrollbar-button, body::-webkit-scrollbar-button { display: none; width: 0; height: 0; }
            .chat-messages { display: flex; flex-direction: column; gap: 0.5rem;
                             min-height: 60vh; max-height: 70vh; overflow-y: scroll;
                             padding: 1rem;
                             scrollbar-width: thin; scrollbar-color: transparent transparent; }
            .chat-messages:hover { scrollbar-color: #555 transparent; }
            .chat-messages::-webkit-scrollbar { width: 6px; }
            .chat-messages::-webkit-scrollbar-track { background: transparent; }
            .chat-messages::-webkit-scrollbar-thumb { background: transparent; border-radius: 3px; }
            .chat-messages:hover::-webkit-scrollbar-thumb { background: #555; }
            .msg-user { align-self: flex-end; background: #1e3a5f; padding: 0.75rem 1rem;
                        border-radius: 1rem 1rem 0.25rem 1rem; max-width: 80%; }
            .msg-ai   { align-self: flex-start; background: #2a2d35; padding: 0.75rem 1rem;
                        border-radius: 1rem 1rem 1rem 0.25rem; max-width: 80%; }
            .msg-ai p { margin: 0.4em 0; }
            .msg-ai ul, .msg-ai ol { margin: 0.4em 0 0.4em 1.2em; padding: 0; }
            .msg-ai li { margin: 0.15em 0; }
            .msg-ai h1, .msg-ai h2, .msg-ai h3, .msg-ai h4 { margin: 0.6em 0 0.3em; }
            .msg-ai code { background: #1a1d27; padding: 0.15em 0.35em; border-radius: 0.25rem; font-size: 0.9em; }
            .msg-ai pre { background: #1a1d27; padding: 0.75rem; border-radius: 0.5rem; overflow-x: auto; }
            .msg-ai pre code { background: none; padding: 0; }
            .typing-indicator { visibility: hidden; align-self: flex-start; color: #888;
                                padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.45rem; }
            .typing-indicator.htmx-request { visibility: visible; }
            .typing-indicator .dot { width: 8px; height: 8px; border-radius: 50%;
                                     background: #888; animation: dotBounce 1.4s ease-in-out infinite; }
            .typing-indicator .dot:nth-child(2) { animation-delay: 0.16s; }
            .typing-indicator .dot:nth-child(3) { animation-delay: 0.32s; }
            @keyframes dotBounce {
                0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
                40% { transform: translateY(-6px); opacity: 1; }
            }
            /* Sidebar */
            .sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 90; }
            .sidebar-overlay.open { display: block; }
            .sidebar { display: none; position: fixed; top: 0; left: 0; width: 300px; height: 100vh;
                       background: #1a1d27; z-index: 100;
                       padding: 1rem; overflow-y: auto; border-right: 1px solid #333; }
            .sidebar.open { display: block; }
            .sidebar-item { padding: 0.75rem; margin: 0.25rem 0; border-radius: 0.5rem;
                            cursor: pointer; border: 1px solid transparent; }
            .sidebar-item:hover { background: #2a2d35; }
            .sidebar-item .last-played { font-size: 0.8rem; color: #888; }
            .sidebar-close { float: right; cursor: pointer; background: none; border: none;
                             color: #aaa; font-size: 1.2rem; }
            .app-brand { font-size: 0.75rem; color: #666; letter-spacing: 0.05em;
                         text-transform: uppercase; margin-left: auto; user-select: none; }
            /* Rename overlay */
            .rename-overlay { display: none; position: fixed; inset: 0;
                              background: rgba(0,0,0,0.5); z-index: 200;
                              justify-content: center; align-items: center; }
            .rename-overlay.open { display: flex; }
            .rename-dialog { background: #1a1d27; padding: 1.5rem; border-radius: 0.75rem;
                             width: 400px; max-width: 90vw; }
            /* Delete confirm */
            .delete-confirm { display: none; padding: 0.75rem; margin-top: 0.5rem;
                              background: #3a1c1c; border-radius: 0.5rem; }
            .delete-confirm.open { display: block; }
            /* Header bar */
            .chat-header { display: flex; align-items: center; gap: 0.75rem; }
            .chat-header h3 { margin: 0; flex: 1; }
            .header-btn { background: none; border: 1px solid #555; color: #ccc;
                          padding: 0.3rem 0.6rem; border-radius: 0.375rem; cursor: pointer;
                          font-size: 0.85rem; }
            .header-btn:hover { background: #2a2d35; }
            /* Chat input */
            .chat-input-wrap { position: relative; display: flex; align-items: flex-end; }
            .chat-input-wrap textarea { width: 100%; resize: none; overflow-y: hidden;
                min-height: 2.6rem; max-height: 8rem; padding: 0.6rem 2.8rem 0.6rem 0.75rem;
                border-radius: 1rem; border: 1px solid #444; background: #1a1d27;
                color: #ddd; font-size: 0.95rem; line-height: 1.4; font-family: inherit;
                box-sizing: border-box; }
            .chat-input-wrap textarea:focus { outline: none; border-color: #5b8dd9; }
            .chat-input-wrap textarea::placeholder { color: #777; }
            button.chat-send-btn[type="submit"] {
                position: absolute !important; right: 0.45rem !important; bottom: 0.4rem !important;
                width: 1.9rem !important; height: 1.9rem !important; min-width: 0 !important;
                border-radius: 50% !important; border: none !important;
                background: #5b8dd9 !important; color: #fff !important;
                cursor: pointer; display: flex !important;
                align-items: center; justify-content: center;
                padding: 0 !important; margin: 0 !important;
                font-size: 1rem; line-height: 1; transition: background 0.15s;
                box-shadow: none !important; }
            button.chat-send-btn[type="submit"]:hover { background: #4a7bc8 !important; }
            button.chat-send-btn svg { width: 1rem; height: 1rem; fill: currentColor; }
            """
        ),
    ),
)


# ── Routes ────────────────────────────────────────────────────────────────


@rt("/")
def get():
    """Root route – redirect based on app state."""
    cfg = _load_config()
    if not cfg.get("api_key"):
        # Check for saved OAuth token
        from .auth import load_token
        saved_token = load_token(DATA_DIR)
        if saved_token:
            cfg["api_key"] = saved_token
            _save_config(cfg)
        else:
            return _welcome_page()
    # If key exists but no playthroughs, go to creation
    db = _get_db()
    row = db.execute("SELECT id FROM playthroughs ORDER BY updated_at DESC, id DESC LIMIT 1").fetchone()
    db.close()
    if not row:
        return _create_playthrough_page()
    # Otherwise show the most recent playthrough's chat
    return _chat_page(row["id"])


# ── Welcome / Setup ──────────────────────────────────────────────────────


def _welcome_page():
    # Check if OAuth client ID is configured
    client_id = os.environ.get("LOREKEEPER_GITHUB_CLIENT_ID", "")
    oauth_section = []
    if client_id:
        oauth_section = [
            H3("Option 1: Sign in with GitHub (recommended)"),
            P("Click the button below to authenticate with your GitHub account. No tokens to copy."),
            Button(
                "Sign in with GitHub",
                hx_post="/auth/github/start",
                hx_target="#auth-status",
                data_testid="github-login-btn",
                style="width: 100%;",
            ),
            Div(id="auth-status"),
            Hr(),
            H3("Option 2: Manual API key"),
        ]
    return Titled(
        "LoreKeeper",
        Div(
            H2("Welcome to LoreKeeper", data_testid="welcome-heading"),
            *oauth_section,
            P(
                "Enter your GitHub token to get started. " if not client_id else "",
                A(
                    "Get a GitHub token →",
                    href="https://github.com/settings/tokens",
                    target="_blank",
                    data_testid="api-key-provider-link",
                ),
            ) if not client_id else P(
                A(
                    "Or generate a Personal Access Token →",
                    href="https://github.com/settings/tokens",
                    target="_blank",
                    data_testid="api-key-provider-link",
                ),
                cls="secondary",
            ),
            P(
                "Optional: Add a Tavily API key to enable web search.",
                cls="secondary",
            ),
            P(
                "Uses your GitHub Copilot token — no extra API key cost.",
                data_testid="api-key-cost-info",
                cls="secondary",
            ),
            Form(
                Input(
                    id="api_key",
                    name="api_key",
                    type="password",
                    placeholder="Paste your API key",
                    data_testid="api-key-input",
                    required=True,
                ),
                Input(
                    id="tavily_api_key",
                    name="tavily_api_key",
                    type="password",
                    placeholder="(Optional) Paste your Tavily API key",
                    data_testid="tavily-key-input",
                ),
                Div(id="api-key-status-container"),
                Div(
                    Button(
                        "Test Key",
                        type="button",
                        cls="secondary outline",
                        hx_post="/api/test-key",
                        hx_include="[name='api_key']",
                        hx_target="#api-key-status-container",
                        data_testid="test-key-btn",
                    ),
                    Button(
                        "Save & Continue",
                        type="submit",
                        data_testid="save-key-btn",
                    ),
                    cls="grid",
                ),
                method="post",
                action="/setup/save-key",
            ),
        ),
    )


@rt("/api/test-key")
def post(api_key: str):
    """HTMX endpoint – validate an API key and return status markup."""
    valid, msg = _validate_api_key(api_key)
    if valid:
        return Span(f"✓ {msg}", data_testid="api-key-status", style="color: #4caf50;")
    return Span(f"✗ {msg}", data_testid="api-key-status", style="color: #f44336;")


@rt("/setup/save-key")
def post(api_key: str, tavily_api_key: str = ""):
    """Save the API key and redirect to playthrough creation."""
    cfg = _load_config()
    cfg["api_key"] = api_key
    if tavily_api_key:
        cfg["tavily_api_key"] = tavily_api_key
    _save_config(cfg)
    return RedirectResponse("/setup/new-playthrough", status_code=303)


# ── GitHub OAuth Device Flow ─────────────────────────────────────────────

# In-memory store for pending device codes (single-user local app)
_pending_device_flow: dict = {}

@rt("/auth/github/start")
def post():
    """Start GitHub OAuth device flow — returns HTMX partial with user code."""
    client_id = os.environ.get("LOREKEEPER_GITHUB_CLIENT_ID", "")
    if not client_id:
        return Div(
            Span("⚠️ GitHub OAuth not configured. Set LOREKEEPER_GITHUB_CLIENT_ID.", style="color: #f44336;"),
            data_testid="auth-error",
        )
    try:
        from .auth import request_device_code
        result = request_device_code(client_id)
        _pending_device_flow["device_code"] = result["device_code"]
        _pending_device_flow["interval"] = result.get("interval", 5)
        _pending_device_flow["expires_in"] = result.get("expires_in", 900)
        _pending_device_flow["client_id"] = client_id
        user_code = result["user_code"]
        verify_uri = result.get("verification_uri", "https://github.com/login/device")
        return Div(
            P(
                "Go to ",
                A(verify_uri, href=verify_uri, target="_blank", style="font-weight: bold;"),
                " and enter this code:",
            ),
            Div(
                Code(user_code, style="font-size: 2em; letter-spacing: 0.2em; padding: 0.5em 1em; background: #1a1f2e; border-radius: 8px; display: inline-block;"),
                style="text-align: center; margin: 1em 0;",
            ),
            P("Waiting for authorization...", cls="secondary"),
            Div(
                id="auth-poll",
                hx_get="/auth/github/poll",
                hx_trigger="every 5s",
                hx_swap="outerHTML",
            ),
            data_testid="auth-device-code",
        )
    except Exception as exc:
        return Div(
            Span(f"⚠️ {exc}", style="color: #f44336;"),
            data_testid="auth-error",
        )


@rt("/auth/github/poll")
def get():
    """Poll for device flow completion — HTMX auto-polls this."""
    if "device_code" not in _pending_device_flow:
        return Div(Span("No pending auth flow.", style="color: #f44336;"))

    client_id = _pending_device_flow["client_id"]
    device_code = _pending_device_flow["device_code"]

    try:
        from .auth import _post_form, _TOKEN_URL
        result = _post_form(_TOKEN_URL, {
            "client_id": client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })

        if "access_token" in result:
            token = result["access_token"]
            cfg = _load_config()
            cfg["api_key"] = token
            _save_config(cfg)
            _pending_device_flow.clear()

            # Save token for persistence
            from .auth import save_token
            save_token(token, DATA_DIR)

            return Div(
                Span("✓ Signed in with GitHub!", style="color: #4caf50; font-weight: bold;"),
                Script("setTimeout(function(){ window.location.href = '/setup/new-playthrough'; }, 1500);"),
                data_testid="auth-success",
            )

        error = result.get("error", "")
        if error == "authorization_pending":
            return Div(
                P("⏳ Waiting for you to enter the code...", cls="secondary"),
                id="auth-poll",
                hx_get="/auth/github/poll",
                hx_trigger="every 5s",
                hx_swap="outerHTML",
            )
        elif error == "slow_down":
            return Div(
                P("⏳ Waiting...", cls="secondary"),
                id="auth-poll",
                hx_get="/auth/github/poll",
                hx_trigger="every 10s",
                hx_swap="outerHTML",
            )
        elif error in ("expired_token", "access_denied"):
            _pending_device_flow.clear()
            return Div(
                Span(f"✗ Authorization {'expired' if error == 'expired_token' else 'denied'}. Try again.",
                     style="color: #f44336;"),
                data_testid="auth-failed",
            )
        else:
            return Div(Span(f"⚠️ {result.get('error_description', error)}", style="color: #f44336;"))

    except Exception as exc:
        return Div(Span(f"⚠️ {exc}", style="color: #f44336;"))


def _settings_page(saved: int = 0):
    cfg = _load_config()
    key_set = "set" if cfg.get("api_key") else "not set"
    tavily_set = "set" if cfg.get("tavily_api_key") else "not set"
    debug_mode = bool(cfg.get("debug_mode"))
    selected_model = cfg.get("model_name", "gpt-4o")
    model_options = _get_available_models(cfg.get("api_key", ""))
    db = _get_db()
    pts = db.execute(
        "SELECT id, name FROM playthroughs ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    db.close()
    return Titled(
        "LoreKeeper",
        Div(
            H2("Settings", data_testid="settings-heading"),
            Form(
                Label(
                    "API Key: ",
                    Span(
                        key_set,
                        data_testid="api-key-status",
                        style=f"color: {'#4caf50' if key_set == 'set' else '#f44336'};",
                    ),
                    Input(
                        id="api_key",
                        name="api_key",
                        type="password",
                        placeholder="Paste your API key",
                        data_testid="api-key-input",
                    ),
                ),
                Label(
                    "Tavily API Key: ",
                    Span(
                        tavily_set,
                        data_testid="tavily-key-status",
                        style=f"color: {'#4caf50' if tavily_set == 'set' else '#f44336'};",
                    ),
                    Input(
                        id="tavily_api_key",
                        name="tavily_api_key",
                        type="password",
                        placeholder="(Optional) Paste your Tavily API key",
                        data_testid="tavily-key-input",
                    ),
                ),
                Label(
                    "AI Model",
                    Select(
                        *[Option(m, value=m, selected=(m == selected_model)) for m in model_options],
                        name="model_name",
                        data_testid="model-select",
                    ),
                ),
                Div(
                    "Add your API key to load models.",
                    cls="secondary",
                ) if not model_options else "",
                Label(
                    Input(
                        id="debug_mode",
                        name="debug_mode",
                        type="checkbox",
                        checked=debug_mode,
                        data_testid="debug-toggle",
                    ),
                    " Enable debug mode (write changelog.jsonl)",
                ),
                Div(
                    "Data location: ",
                    Span(str(DATA_DIR.resolve()), data_testid="data-location"),
                ),
                Button("Save Settings", type="submit", data_testid="settings-save-btn"),
                Div(
                    "Settings saved.",
                    data_testid="settings-saved",
                    cls="secondary",
                ) if saved else "",
                method="post",
                action="/settings/save",
            ),
            Hr(),
            H3("Export Playthrough"),
            Form(
                Select(
                    *[Option(p["name"], value=p["id"]) for p in pts],
                    name="playthrough_id",
                ),
                Button("Export", type="submit", data_testid="export-playthrough-btn"),
                method="get",
                action="/playthrough/export",
            ),
            Hr(),
            H3("Import Playthrough"),
            Form(
                Input(
                    type="file",
                    name="import_file",
                    data_testid="import-file-input",
                    required=True,
                ),
                Button("Import", type="submit", data_testid="import-playthrough-btn"),
                method="post",
                action="/playthrough/import",
                enctype="multipart/form-data",
            ),
        ),
    )


@rt("/settings")
def get(saved: int = 0):
    return _settings_page(saved)


@rt("/settings/save")
def post(
    api_key: str = "",
    tavily_api_key: str = "",
    debug_mode: str = "",
    model_name: str = "",
):
    cfg = _load_config()
    if api_key:
        cfg["api_key"] = api_key
    if tavily_api_key:
        cfg["tavily_api_key"] = tavily_api_key
    if model_name:
        cfg["model_name"] = model_name
    cfg["debug_mode"] = bool(debug_mode)
    _save_config(cfg)
    return RedirectResponse("/settings?saved=1", status_code=303)


@rt("/setup/new-playthrough")
def get():
    return _create_playthrough_page()


# ── Playthrough Creation ─────────────────────────────────────────────────


def _create_playthrough_page():
    return Titled(
        "New Playthrough",
        Div(
            H2("Create Your First Playthrough", data_testid="create-playthrough-heading"),
            Form(
                Label(
                    "Playthrough Name",
                    Input(
                        id="name",
                        name="name",
                        placeholder='e.g. "BG3 – Dark Urge Run"',
                        data_testid="playthrough-name-input",
                        required=True,
                    ),
                ),
                Label(
                    "Game Title (optional)",
                    Input(
                        id="game_title",
                        name="game_title",
                        placeholder='e.g. "Baldur\'s Gate 3"',
                        data_testid="game-title-input",
                    ),
                ),
                Button("Create Playthrough", type="submit", data_testid="create-playthrough-btn"),
                method="post",
                action="/playthrough/create",
            ),
        ),
    )


def _welcome_message_text(game_title: str = "") -> str:
    game_title = (game_title or "").strip()
    if game_title:
        return (
            "Hi! I’m LoreKeeper — your game companion for tracking builds, "
            "party details, and story progress.\n\n"
            f"I see you’re playing {game_title}. Who’s your character?"
        )
    return (
        "Hi! I’m LoreKeeper — your game companion for tracking builds, "
        "party details, and story progress.\n\n"
        "What are you playing, and who’s your character?"
    )


@rt("/playthrough/create")
def post(name: str, game_title: str = ""):
    """Create a new playthrough and redirect to its chat."""
    db = _get_db()
    cur = db.execute(
        "INSERT INTO playthroughs (name, game_title) VALUES (?, ?)",
        (name, game_title),
    )
    db.commit()
    pid = cur.lastrowid
    welcome_text = _welcome_message_text(game_title)
    db.execute(
        "INSERT INTO messages (playthrough_id, role, content) VALUES (?, 'assistant', ?)",
        (pid, welcome_text),
    )
    db.commit()
    db.close()
    return RedirectResponse(f"/chat/{pid}", status_code=303)


# ── Chat ──────────────────────────────────────────────────────────────────


def _chat_page(playthrough_id: int):
    db = _get_db()
    pt = db.execute("SELECT * FROM playthroughs WHERE id = ?", (playthrough_id,)).fetchone()
    msgs = db.execute(
        "SELECT * FROM messages WHERE playthrough_id = ? ORDER BY created_at",
        (playthrough_id,),
    ).fetchall()
    # Update last-active timestamp when viewing a playthrough
    db.execute(
        "UPDATE playthroughs SET updated_at = datetime('now') WHERE id = ?",
        (playthrough_id,),
    )
    db.commit()
    all_pts = db.execute(
        "SELECT * FROM playthroughs ORDER BY updated_at DESC, id DESC"
    ).fetchall()
    db.close()

    if not pt:
        return RedirectResponse("/", status_code=303)

    message_els = []
    if not msgs:
        welcome_text = _welcome_message_text(pt["game_title"] if pt else "")
        message_els.append(
            Div(
                _render_ai_message(welcome_text),
                cls="msg-ai",
                data_testid="ai-message",
            )
        )
    for m in msgs:
        if m["role"] == "user":
            message_els.append(
                Div(m["content"], cls="msg-user", data_testid="user-message")
            )
        else:
            message_els.append(
                Div(_render_ai_message(m["content"]), cls="msg-ai", data_testid="ai-message")
            )

    # Build sidebar items
    sidebar_items = []
    for p in all_pts:
        updated = p["updated_at"] or p["created_at"] or ""
        sidebar_items.append(
            A(
                Div(
                    Div(p["name"]),
                    Div(f"Last played: {updated[:16]}", cls="last-played",
                        data_testid="playthrough-last-played"),
                    cls="sidebar-item",
                    data_testid="playthrough-item",
                ),
                href=f"/chat/{p['id']}",
                style="text-decoration:none; color:inherit;",
            )
        )

    return Titled(
        "LoreKeeper",
        # Sidebar overlay + panel
        Div(
            id="sidebar-overlay", cls="sidebar-overlay",
            onclick="this.classList.remove('open'); document.getElementById('sidebar').classList.remove('open');",
        ),
        Div(
            Div(
                Button("✕", cls="sidebar-close",
                       onclick="document.getElementById('sidebar').classList.remove('open'); document.getElementById('sidebar-overlay').classList.remove('open');"),
                H3("Playthroughs"),
            ),
            A(
                Button("+ New Playthrough", cls="outline", style="width:100%; margin-bottom:0.75rem;",
                       data_testid="new-playthrough-btn"),
                href="/setup/new-playthrough",
                style="text-decoration:none;",
            ),
            *sidebar_items,
            id="sidebar", cls="sidebar",
            data_testid="playthrough-sidebar",
        ),
        # Main content
        Div(
            # Header with sidebar toggle, title, rename, delete
            Div(
                Button("☰", cls="header-btn", data_testid="sidebar-toggle",
                       onclick="document.getElementById('sidebar').classList.add('open'); document.getElementById('sidebar-overlay').classList.add('open');"),
                H3(pt["name"], data_testid="playthrough-title"),
                  A(
                      Button("⚙️", cls="header-btn", data_testid="settings-btn"),
                      href="/settings",
                      style="text-decoration:none;",
                  ),
                Button("✏️", cls="header-btn", data_testid="rename-btn",
                       onclick="document.getElementById('rename-overlay').classList.add('open');"),
                Button("🗑️", cls="header-btn", data_testid="delete-btn",
                       onclick="document.getElementById('delete-confirm').classList.add('open');"),
                cls="chat-header",
            ),
            # Delete confirmation
            Div(
                P("Are you sure you want to delete this playthrough? This cannot be undone."),
                Div(
                    A(
                        Button("Yes, delete", cls="contrast", data_testid="delete-confirm-btn"),
                        href=f"/playthrough/{playthrough_id}/delete",
                        style="text-decoration:none;",
                    ),
                    Button("Cancel", cls="outline", data_testid="delete-cancel-btn",
                           onclick="document.getElementById('delete-confirm').classList.remove('open');"),
                    cls="grid",
                ),
                id="delete-confirm", cls="delete-confirm",
            ),
            # Chat messages
            Div(
                *message_els,
                Div(
                    Span(cls="dot"), Span(cls="dot"), Span(cls="dot"),
                    cls="typing-indicator",
                    id="typing-indicator",
                    data_testid="typing-indicator",
                ),
                id="chat-messages",
                cls="chat-messages",
            ),
            # Message input
            Form(
                Div(
                    Textarea(
                        id="message",
                        name="message",
                        placeholder="Type a message…",
                        data_testid="message-input",
                        rows="1",
                        required=True,
                        oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,128)+'px';this.style.overflowY=this.scrollHeight>128?'auto':'hidden';",
                    ),
                    Button(
                        NotStr('<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>'),
                        type="submit",
                        data_testid="send-btn",
                        cls="chat-send-btn",
                        title="Send",
                    ),
                    cls="chat-input-wrap",
                ),
                hx_post=f"/chat/{playthrough_id}/send",
                hx_target="#chat-messages",
                hx_swap="innerHTML",
                hx_indicator="#typing-indicator",
            ),
            # Enter sends, Shift+Enter adds newline; optimistic user bubble + scroll
            Script("""
                (function() {
                    var ta = document.getElementById('message');
                    ta.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            this.closest('form').requestSubmit();
                        }
                    });
                    document.body.addEventListener('htmx:beforeRequest', function(e) {
                        if (e.detail.elt && e.detail.elt.closest && e.detail.elt.closest('form')) {
                            var text = ta.value.trim();
                            if (!text) return;
                            var cm = document.getElementById('chat-messages');
                            var indicator = document.getElementById('typing-indicator');
                            var bubble = document.createElement('div');
                            bubble.className = 'msg-user';
                            bubble.setAttribute('data-testid', 'user-message');
                            bubble.textContent = text;
                            cm.insertBefore(bubble, indicator);
                            ta.value = '';
                            ta.style.height = 'auto';
                            cm.scrollTop = cm.scrollHeight;
                        }
                    });
                    document.body.addEventListener('htmx:afterRequest', function(e) {
                        if (e.detail.elt && e.detail.elt.closest && e.detail.elt.closest('form')) {
                            var cm = document.getElementById('chat-messages');
                            if (cm) cm.scrollTop = cm.scrollHeight;
                        }
                    });
                })();
            """),
            data_testid="chat-container",
        ),
        # Rename overlay (modal)
        Div(
            Div(
                H3("Rename Playthrough"),
                Form(
                    Label(
                        "Name",
                        Input(id="rename_name", name="name", value=pt["name"],
                              data_testid="rename-name-input"),
                    ),
                    Label(
                        "Game Title",
                        Input(id="rename_game_title", name="game_title",
                              value=pt["game_title"] or "",
                              data_testid="rename-game-title-input"),
                    ),
                    Div(
                        Button("Save", type="submit", data_testid="rename-save-btn"),
                        Button("Cancel", type="button", cls="outline",
                               onclick="document.getElementById('rename-overlay').classList.remove('open');"),
                        cls="grid",
                    ),
                    method="post",
                    action=f"/playthrough/{playthrough_id}/rename",
                ),
                cls="rename-dialog",
            ),
            id="rename-overlay", cls="rename-overlay",
        ),
    )


@rt("/chat/{playthrough_id}")
def get(playthrough_id: int):
    return _chat_page(playthrough_id)


@rt("/chat/{playthrough_id}/send")
def post(playthrough_id: int, message: str):
    """Handle a chat message: save user message, get AI response, save & return."""
    db = _get_db()
    cfg = _load_config()

    offline_reply = None
    if _is_offline(cfg):
        offline_reply = "⚠️ You're offline. Connect to the internet to continue chatting."

    # Save user message
    cur = db.execute(
        "INSERT INTO messages (playthrough_id, role, content) VALUES (?, 'user', ?)",
        (playthrough_id, message),
    )
    db.commit()
    user_msg_id = cur.lastrowid

    # Load playthrough info for system prompt
    pt = db.execute(
        "SELECT name, game_title FROM playthroughs WHERE id = ?",
        (playthrough_id,),
    ).fetchone()

    # Build RAG context for this query
    rag_context = _build_rag_context(db, playthrough_id, message)
    stable_context = _load_stable_context(db, playthrough_id)

    # Handle memory-view queries directly (no LLM call)
    memory_reply = _maybe_handle_memory_query(message, stable_context)
    if offline_reply:
        memory_reply = offline_reply

    # Generate AI response via M4 structured-output orchestration
    try:
        deltas: list[dict] = []
        if memory_reply is not None:
            ai_text = memory_reply
            raw_response = None
        elif TEST_MODE:
            if cfg.get("force_api_error"):
                raise RuntimeError(str(cfg.get("force_api_error")))
            raw_response = _mock_llm_respond(
                message, rag_context, stable_context=stable_context
            )
        else:
            # Build conversation history for LLM
            past_msgs = db.execute(
                "SELECT role, content FROM messages WHERE playthrough_id = ? ORDER BY created_at",
                (playthrough_id,),
            ).fetchall()
            history = []
            for m in past_msgs:
                # Skip the message we just inserted — it'll be sent as the new user turn
                if m["role"] == "user" and m["content"] == message and m is past_msgs[-1]:
                    continue
                llm_role = "user" if m["role"] == "user" else "assistant"
                history.append({"role": llm_role, "content": m["content"]})

            system_prompt = _build_system_prompt(
                pt["name"] if pt else "",
                pt["game_title"] if pt else "",
            )
            system_prompt += "\n\n" + _stable_context_to_text(stable_context)
            if rag_context:
                system_prompt += "\n\nRelevant prior context:\n" + rag_context
            system_prompt += _STRUCTURED_OUTPUT_INSTRUCTIONS
            api_key = cfg.get("api_key", "")
            model_name = cfg.get("model_name", "gpt-4o")
            raw_response = _call_llm(api_key, system_prompt, history, message, model_name=model_name)

        # Parse structured JSON (with plain-text fallback)
        if raw_response is not None:
            parsed = _parse_llm_response(raw_response)
            ai_text = parsed["response"]
            # Strip echo: LLM sometimes repeats the user's message at the start
            if ai_text and message and ai_text.lstrip().startswith(message.strip()):
                ai_text = ai_text.lstrip()[len(message.strip()):].lstrip()
                if not ai_text:
                    ai_text = parsed["response"]  # revert if nothing left
            # Strip leaked JSON blobs (LLM sometimes dumps stable context)
            ai_text = _strip_json_blobs(ai_text)
            deltas = parsed.get("context_deltas", []) or []
            web_search = parsed.get("web_search")
            # If blob-stripping emptied the response, generate a friendly fallback
            if not ai_text.strip():
                ai_text = "Got it — I've updated my notes."
        else:
            web_search = None
        search_unavailable = False

        # If LLM flagged a web search, execute it and make a second call
        if web_search and isinstance(web_search, dict) and web_search.get("query"):
            search_query = web_search["query"]

            if TEST_MODE:
                search_results = _mock_tavily_search(search_query)
            else:
                tavily_key = cfg.get(
                    "tavily_api_key", os.environ.get("TAVILY_API_KEY", "")
                )
                if tavily_key:
                    search_results = _call_tavily_search(tavily_key, search_query)
                    if search_results is None:
                        search_results = []
                        search_unavailable = True
                else:
                    search_results = []
                    search_unavailable = True

            if search_results:
                search_context = _format_search_results(search_results)

                if TEST_MODE:
                    raw_response2 = _mock_llm_respond(
                        message,
                        rag_context,
                        search_results=search_context,
                        stable_context=stable_context,
                    )
                else:
                    system_prompt2 = (
                        system_prompt
                        + _SEARCH_CITATION_INSTRUCTIONS
                        + "\n"
                        + search_context
                    )
                    raw_response2 = _call_llm(
                        api_key, system_prompt2, history, message, model_name=model_name
                    )

                parsed2 = _parse_llm_response(raw_response2)
                ai_text = parsed2["response"]
                deltas = parsed2.get("context_deltas", []) or []
            elif search_unavailable:
                ai_text = "Web search is unavailable — add a Tavily API key in Settings."

        # Apply stable context deltas (if any)
        applied = 0
        if deltas:
            applied = _apply_context_deltas(db, playthrough_id, deltas)
            if applied > 0 and _load_config().get("debug_mode"):
                _append_changelog(playthrough_id, deltas)
        if applied > 0:
            summary, _ = _summarize_context_deltas(deltas)
            ai_text = f"{ai_text}\n\n📌 {summary}"

        if search_unavailable and "Web search unavailable" not in ai_text:
            ai_text = (
                f"{ai_text}\n\n"
                "(Web search unavailable — add a Tavily API key in Settings.)"
            )

        if not ai_text or not ai_text.strip():
            ai_text = "⚠️ Empty response from model. Please try again."

    except Exception as exc:
        ai_text = _format_api_error(exc)

    # Save AI response
    cur = db.execute(
        "INSERT INTO messages (playthrough_id, role, content) VALUES (?, 'assistant', ?)",
        (playthrough_id, ai_text),
    )
    ai_msg_id = cur.lastrowid

    # Index both messages for RAG
    _rag_index_message(db, playthrough_id, user_msg_id, "user", message)
    _rag_index_message(db, playthrough_id, ai_msg_id, "assistant", ai_text)

    # Update playthrough timestamp
    db.execute(
        "UPDATE playthroughs SET updated_at = datetime('now') WHERE id = ?",
        (playthrough_id,),
    )
    db.commit()

    # Return updated message list (HTMX swaps innerHTML of #chat-messages)
    msgs = db.execute(
        "SELECT * FROM messages WHERE playthrough_id = ? ORDER BY created_at",
        (playthrough_id,),
    ).fetchall()
    db.close()

    els = []
    for m in msgs:
        if m["role"] == "user":
            els.append(Div(m["content"], cls="msg-user", data_testid="user-message"))
        else:
            els.append(Div(_render_ai_message(m["content"]), cls="msg-ai", data_testid="ai-message"))
    els.append(
        Div(
            Span(cls="dot"), Span(cls="dot"), Span(cls="dot"),
            cls="typing-indicator",
            id="typing-indicator",
            data_testid="typing-indicator",
        )
    )
    return tuple(els)


# ── Rename / Delete ───────────────────────────────────────────────────────


@rt("/playthrough/{playthrough_id}/rename")
def post(playthrough_id: int, name: str, game_title: str = ""):
    """Rename a playthrough and/or update its game title."""
    db = _get_db()
    db.execute(
        "UPDATE playthroughs SET name = ?, game_title = ?, updated_at = datetime('now') WHERE id = ?",
        (name, game_title, playthrough_id),
    )
    db.commit()
    db.close()
    return RedirectResponse(f"/chat/{playthrough_id}", status_code=303)


@rt("/playthrough/{playthrough_id}/delete")
def get(playthrough_id: int):
    """Delete a playthrough and all its messages."""
    db = _get_db()
    db.execute("DELETE FROM graph_edges WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM graph_nodes WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM rag_chunks WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM messages WHERE playthrough_id = ?", (playthrough_id,))
    db.execute("DELETE FROM playthroughs WHERE id = ?", (playthrough_id,))
    db.commit()
    # Check if any playthroughs remain
    remaining = db.execute("SELECT id FROM playthroughs ORDER BY updated_at DESC, id DESC LIMIT 1").fetchone()
    db.close()
    if remaining:
        return RedirectResponse(f"/chat/{remaining['id']}", status_code=303)
    return RedirectResponse("/setup/new-playthrough", status_code=303)


@rt("/playthrough/export")
def get(playthrough_id: int):
    db = _get_db()
    pt = db.execute(
        "SELECT id, name, game_title, created_at, updated_at FROM playthroughs WHERE id = ?",
        (playthrough_id,),
    ).fetchone()
    msgs = db.execute(
        "SELECT role, content, created_at FROM messages WHERE playthrough_id = ? ORDER BY created_at",
        (playthrough_id,),
    ).fetchall()
    stable_context = _load_stable_context(db, playthrough_id)
    db.close()

    payload = {
        "playthrough": dict(pt) if pt else {},
        "messages": [dict(m) for m in msgs],
        "stable_context": stable_context,
    }
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("playthrough.json", json.dumps(payload["playthrough"]))
        zf.writestr("messages.json", json.dumps(payload["messages"]))
        zf.writestr("stable_context.json", json.dumps(payload["stable_context"]))
    mem.seek(0)
    filename = f"playthrough_{playthrough_id}.zip"
    return StreamingResponse(
        mem,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@rt("/playthrough/import")
def post(import_file: UploadFile):
    data = import_file.file.read()
    mem = io.BytesIO(data)
    with zipfile.ZipFile(mem, "r") as zf:
        playthrough = json.loads(zf.read("playthrough.json"))
        messages = json.loads(zf.read("messages.json"))
        stable_context = json.loads(zf.read("stable_context.json"))

    db = _get_db()
    name = playthrough.get("name", "Imported Playthrough")
    game_title = playthrough.get("game_title", "")
    existing = db.execute("SELECT id FROM playthroughs WHERE name = ?", (name,)).fetchone()
    if existing:
        name = f"{name} (Imported)"
    cur = db.execute(
        "INSERT INTO playthroughs (name, game_title) VALUES (?, ?)",
        (name, game_title),
    )
    db.commit()
    playthrough_id = cur.lastrowid

    for node in stable_context.get("nodes", []) or []:
        _upsert_node(db, playthrough_id, node["name"], node["kind"],
                     node.get("properties", {}), node.get("status", "active"))
    for edge in stable_context.get("edges", []) or []:
        _add_edge(db, playthrough_id, edge["source"], edge["target"],
                  edge["label"], edge.get("properties", {}))

    for m in messages:
        cur = db.execute(
            "INSERT INTO messages (playthrough_id, role, content) VALUES (?, ?, ?)",
            (playthrough_id, m.get("role", "user"), m.get("content", "")),
        )
        msg_id = cur.lastrowid
        _rag_index_message(db, playthrough_id, msg_id, m.get("role", "user"), m.get("content", ""))
    db.commit()
    db.close()
    return RedirectResponse(f"/chat/{playthrough_id}", status_code=303)


# ── Test-mode-only reset endpoint ─────────────────────────────────────────

if TEST_MODE:

    @rt("/test/reset")
    def post():
        """Wipe all data and return the app to a fresh-install state."""
        db = _get_db()
        db.execute("DELETE FROM graph_edges")
        db.execute("DELETE FROM graph_nodes")
        db.execute("DELETE FROM rag_chunks")
        db.execute("DELETE FROM messages")
        db.execute("DELETE FROM playthroughs")
        db.commit()
        db.close()
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
        return "ok"

    @rt("/test/inject-messages")
    def post(playthrough_id: int, messages: str):
        """Seed messages into DB + RAG index for testing."""
        db = _get_db()
        msg_list = json.loads(messages)
        for msg in msg_list:
            cur = db.execute(
                "INSERT INTO messages (playthrough_id, role, content) VALUES (?, ?, ?)",
                (playthrough_id, msg["role"], msg["content"]),
            )
            msg_id = cur.lastrowid
            _rag_index_message(db, playthrough_id, msg_id, msg["role"], msg["content"])
        db.commit()
        db.close()
        return f"ok: injected {len(msg_list)} messages"

    @rt("/test/set-config")
    async def post(request: Request):
        body = await request.body()
        data = json.loads(body.decode("utf-8") or "{}")
        cfg = _load_config()
        cfg.update(data)
        _save_config(cfg)
        return JSONResponse({"ok": True})

    @rt("/test/changelog")
    def get():
        path = DATA_DIR / "changelog.jsonl"
        if not path.exists():
            return JSONResponse({"lines": []})
        lines = path.read_text(encoding="utf-8").splitlines()
        return JSONResponse({"lines": lines})

    @rt("/test/get-config")
    def get():
        return JSONResponse(_load_config())

    @rt("/test/rag-stats")
    def get(playthrough_id: int):
        """Return RAG index statistics for a playthrough."""
        db = _get_db()
        row = db.execute(
            "SELECT COUNT(*) as c FROM rag_chunks WHERE playthrough_id = ?",
            (playthrough_id,),
        ).fetchone()
        db.close()
        return JSONResponse({"indexed_count": row["c"]})


# ── Entry point ───────────────────────────────────────────────────────────


def run():
    """CLI entry point (via pyproject.toml console_scripts)."""
    serve(port=PORT)


serve(port=PORT)
