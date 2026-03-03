from __future__ import annotations

import json
import re
import sqlite3


def _get_all_nodes(db: sqlite3.Connection, playthrough_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT name, kind, properties_json, status FROM graph_nodes "
        "WHERE playthrough_id = ?",
        (playthrough_id,),
    ).fetchall()
    return [
        {
            "name": r["name"],
            "kind": r["kind"],
            "properties": json.loads(r["properties_json"]),
            "status": r["status"],
        }
        for r in rows
    ]


def _get_all_edges(db: sqlite3.Connection, playthrough_id: int) -> list[dict]:
    rows = db.execute(
        "SELECT s.name AS source, t.name AS target, e.label, e.properties_json "
        "FROM graph_edges e "
        "JOIN graph_nodes s ON e.source_id = s.id "
        "JOIN graph_nodes t ON e.target_id = t.id "
        "WHERE e.playthrough_id = ?",
        (playthrough_id,),
    ).fetchall()
    return [
        {
            "source": r["source"],
            "target": r["target"],
            "label": r["label"],
            "properties": json.loads(r["properties_json"]),
        }
        for r in rows
    ]


def _load_stable_context(db: sqlite3.Connection, playthrough_id: int) -> dict:
    """Load the full knowledge graph for a playthrough."""
    return {
        "nodes": _get_all_nodes(db, playthrough_id),
        "edges": _get_all_edges(db, playthrough_id),
    }


def _build_character_sheet(ctx: dict, name: str) -> str | None:
    """Build a character sheet view from stable context."""
    nodes = ctx.get("nodes", [])
    node = next(
        (
            n
            for n in nodes
            if n.get("name", "").lower() == name.lower()
            and n.get("kind") == "character"
        ),
        None,
    )
    if not node:
        return None

    props = node.get("properties", {})
    lines = [f"Character Sheet - {node.get('name', 'Unknown')}"]
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


def _build_party_summary(ctx: dict) -> str:
    """Build a summary of party members from stable context."""
    characters = [n for n in ctx.get("nodes", []) if n.get("kind") == "character"]
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


def _build_memory_query_response(message: str, ctx: dict) -> str | None:
    """Build direct memory/context responses without an LLM call."""
    text = message.strip()
    lower = text.lower()

    if "what do you remember about my party" in lower:
        return _build_party_summary(ctx)

    match = re.search(r"show me (.+?)'s character sheet", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        return _build_character_sheet(ctx, name) or f"I don't have a character sheet for {name} yet."

    match = re.search(r"show me (.+?)'s stats", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        return _build_character_sheet(ctx, name) or f"I don't have stats for {name} yet."

    return None
