from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter

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


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def _vectorize(text: str) -> Counter:
    return Counter(_tokenize(text))


def _cosine_sim(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a.keys()) & set(b.keys())
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _rag_index_message(
    db: sqlite3.Connection,
    playthrough_id: int,
    message_id: int,
    role: str,
    content: str,
):
    tokens = _vectorize(content)
    db.execute(
        "INSERT INTO rag_chunks (playthrough_id, message_id, role, content, tokens_json) VALUES (?, ?, ?, ?, ?)",
        (playthrough_id, message_id, role, content, json.dumps(tokens)),
    )


def _rag_recent_message_ids(db: sqlite3.Connection, playthrough_id: int) -> set[int]:
    rows = db.execute(
        "SELECT id FROM messages WHERE playthrough_id = ? ORDER BY id DESC LIMIT ?",
        (playthrough_id, RECENT_WINDOW_SIZE),
    ).fetchall()
    return {r["id"] for r in rows}


def _rag_retrieve(
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


def _build_rag_context(
    db: sqlite3.Connection,
    playthrough_id: int,
    user_message: str,
) -> str:
    recent_ids = _rag_recent_message_ids(db, playthrough_id)
    chunks = _rag_retrieve(db, playthrough_id, user_message, exclude_message_ids=recent_ids)
    if not chunks:
        return ""
    return "\n".join(chunks)
