# Game Companion – Technical Design Session

**Date:** February 5, 2026  
**Status:** 🟢 In Progress – M1 Decisions Made  
**Input Document:** [spec.md](spec.md) (v3.0 – Product Requirements)  
**Test Reference:** [test-spec.md](test-spec.md) (v3.0 – Product Test Specification)  

---

## Purpose

This document is the engineering team's space to make **all technical decisions from scratch**, guided only by the product spec. There is no prior implementation to port from — every choice should be made using best practices for the chosen platform.

> **Guiding principle:** The product spec defines *what* the app does. This document defines *how* it's built.

---

## Decisions to Make

The following areas require technical design decisions. Each should be evaluated independently, with no assumptions carried over from prior implementations.

### 1. Language & Runtime

| Question | Notes |
|----------|-------|
| Primary language? | Product spec is platform-agnostic; team has chosen Python |
| Python version? | |
| Package manager? | pip, poetry, uv, etc. |
| Project structure? | Monorepo, src layout, flat, etc. |

### 2. Web Framework & Server

| Question | Notes |
|----------|-------|
| Backend framework? | FastAPI, Flask, Django, Litestar, etc. |
| How are static files served? | Bundled, separate, CDN, etc. |
| Frontend approach? | Server-rendered templates, SPA (React/Vue/Svelte), vanilla JS, HTMX, etc. |
| Real-time updates? | WebSocket, SSE, polling (for typing indicator, streaming responses) |
| How does the user start the app? | `python -m gamecompanion`, script entry point, etc. |

### 3. Data Storage

| Question | Notes |
|----------|-------|
| Database engine? | SQLite, DuckDB, etc. |
| ORM or raw SQL? | SQLAlchemy, Peewee, raw sqlite3, etc. |
| Schema migration strategy? | Alembic, manual versioning, etc. |
| Where is the DB file stored? | User data directory, app directory, configurable? |

### 4. Vector Search / Embeddings

| Question | Notes |
|----------|-------|
| Embedding model? | Gemini embeddings, sentence-transformers (local), etc. |
| Vector storage? | sqlite-vec, ChromaDB, FAISS, Qdrant, in-memory, etc. |
| Chunking strategy? | Fixed-size, semantic, by message, etc. |
| Hybrid search? | Vector + keyword, vector only, etc. |

### 5. LLM Integration

| Question | Notes |
|----------|-------|
| Gemini client library? | google-generativeai, litellm, raw HTTP, etc. |
| Abstraction layer design? | Interface/ABC, strategy pattern, adapter, etc. |
| Structured output approach? | Function calling, JSON mode, response parsing, etc. |
| Streaming? | Stream tokens to UI, or wait for full response? |
| Prompt management? | Templates in code, separate files, prompt library, etc. |

### 6. Web Search Integration

| Question | Notes |
|----------|-------|
| Search provider? | Tavily, SerpAPI, Brave Search, DuckDuckGo, etc. |
| Search trigger logic? | Keyword heuristics, LLM-decided, always-on, etc. |
| Citation formatting? | Inline, footnotes, sidebar, etc. |
| Result caching? | Cache identical queries? TTL? |

### 7. Security & Configuration

| Question | Notes |
|----------|-------|
| API key storage? | keyring, encrypted file, environment variables, etc. |
| Configuration format? | TOML, YAML, JSON, .env, etc. |
| Secrets management in dev? | .env files, direnv, etc. |

### 8. Testing Strategy

| Question | Notes |
|----------|-------|
| Test framework? | pytest, unittest, etc. |
| Async testing? | pytest-asyncio, anyio, etc. |
| API testing? | httpx TestClient, requests-mock, etc. |
| Mocking approach? | unittest.mock, pytest-mock, monkeypatch, etc. |
| CI/CD? | GitHub Actions, manual, etc. |
| Coverage target? | |

### 9. UI & UX Decisions

| Question | Notes |
|----------|-------|
| CSS framework? | Tailwind, Bootstrap, Pico, custom, etc. |
| Dark mode implementation? | CSS variables, prefers-color-scheme, toggle, etc. |
| Markdown rendering? | Server-side, client-side (marked.js, markdown-it), etc. |
| Chat UX pattern? | Scroll behavior, message grouping, timestamps, etc. |
| Memory indicator design? | Toast, inline badge, sidebar, etc. |
| Accessibility considerations? | ARIA labels, keyboard navigation, screen reader support |

### 10. Deployment & Distribution

| Question | Notes |
|----------|-------|
| How does user install? | pip install, git clone + script, standalone executable, etc. |
| How does user launch? | CLI command, double-click, browser bookmark, etc. |
| Auto-open browser? | On server start? |
| Graceful shutdown? | Signal handling, cleanup, etc. |

---

## Architecture Diagram

*To be created by engineering team during design session.*

---

## Chat + Stable Context Orchestration (M5 Critical Path)

> **Status:** Decided 2026-02-05. This is the core workflow of the entire app.
> **Implements:** spec.md §4.3.7–4.3.9, §6.4–6.8
> **Relevant milestones:** M3 (RAG recall), M4 (web search), M5 (living memory)

### The Problem

Every user message must potentially: (a) get an AI response, (b) trigger a web search, and (c) update stable context. A naive design burns 2–3 LLM calls per message. We need one call in the common case.

### Decided Architecture: Single-Call with Optional Search Follow-Up

```
User submits message
  │
  ├─ 1. Orchestrator assembles prompt:
  │      • System prompt (with structured output instructions)
  │      • Stable context (all 5 types, ~3,450 tokens)
  │      • RAG chunks (query-relevant history, ~4,000–6,000 tokens)
  │      • Recent conversation (last 5–10 turns, ~2,000 tokens)
  │      • User's new message
  │
  ├─ 2. ONE LLM call → structured JSON response:
  │      {
  │        "response": "natural language reply to the user",
  │        "context_deltas": [ ...delta operations, or empty... ],
  │        "web_search": null | { "query": "...", "reason": "..." }
  │      }
  │
  ├─ 3. If web_search is non-null:
  │      • Execute search (Tavily/etc.)
  │      • SECOND LLM call with search results appended to context
  │      • This call ALSO returns response + context_deltas
  │      • (Replaces the response/deltas from call #1)
  │
  ├─ 4. Apply context_deltas to SQLite stable context store
  │
  └─ 5. Return response to UI + "📌 Memory updated" indicators if deltas applied
```

**Common path (no search): 1 LLM call.**
**Search path: 2 LLM calls** (one to discover search is needed, one with results).

### Structured Output Format

The system prompt instructs the model to always return JSON:

```json
{
  "response": "Here's what I'd recommend for your next feat...",
  "context_deltas": [
    {
      "type": "entity_sheet",
      "entity": "Keth",
      "operation": "update",
      "path": "state.keyAbilities",
      "value": ["Shadow Step", "Uncanny Dodge", "Extra Attack"],
      "reason": "Player said Keth hit Monk 5 and gained Extra Attack"
    },
    {
      "type": "decision_log",
      "operation": "add",
      "value": {
        "decision": "Took Alert feat over Sentinel",
        "reason": "Initiative control fits shadow-ambush playstyle",
        "consequences": [],
        "status": "active",
        "when": "Level 8"
      },
      "reason": "Player confirmed feat choice"
    }
  ],
  "web_search": null
}
```

Delta operations:
- `update` — set a field at the given path
- `add` — append to an array or create a new entry (new entity, new decision, etc.)
- `remove` — delete an entry (entity archived, decision resolved, etc.)
- `create_entity` — new entity sheet at a given tier (full/summary)

Each delta includes a `reason` field so the "📌 Memory updated" toast can say *what* changed.

### Critical Design Rule: Only User Messages Trigger Deltas

The AI's own response text NEVER triggers stable context updates. Only the user's input does.

Rationale: Stable context tracks **player state and player decisions**. The AI gives advice — it doesn't change the game. The model reads the user's message, writes its reply, and *in the same inference pass* decides what changed. By the time it's composed the response, it already knows whether anything in the user's message warrants a context update.

| User says | AI responds | Context update? | Why |
|-----------|------------|----------------|-----|
| "I just hit level 9" | "Nice! Here's what you unlock..." | ✅ Yes | User stated a fact about game state |
| "What feat should I take?" | "I'd recommend Alert..." | ❌ No | User hasn't decided anything yet |
| "Good call, I'll take Alert" | "Great choice..." | ✅ Yes | User confirmed a decision |
| "I'm in the Shadow-Cursed Lands" | "Be careful, you'll need..." | ✅ Yes | User stated location → AI infers Act 2 progression |

The one edge case — AI inferring something implicit (e.g., "Shadow-Cursed Lands" → Act 2) — is fine. The *trigger* is still the user's message. The AI just does the inference.

### Why Not Always Web Search?

Considered: "Just search every time — saves an LLM call asking whether to search."

Rejected because:
- Most messages don't need search ("I hit level 9", "Show me Alfira's sheet", "Remember this")
- Search adds ~500ms–1s latency per message even when results are useless
- In the one-call design, the search decision costs **zero extra tokens** — it's a JSON field in the response we're already generating
- Only costs an extra call when search IS needed (the uncommon path)

### Orchestrator Responsibilities (Python Backend)

1. **Assemble prompt** — stable context + RAG + recent turns + user message
2. **Parse structured JSON response** — validate schema, extract response/deltas/search flag
3. **Optional search follow-up** — if `web_search` non-null, search + second LLM call
4. **Apply deltas** — update SQLite stable context tables transactionally
5. **Return to UI** — the `response` field + any "📌" indicators for applied deltas
6. **Index to RAG** — store the user message + AI response as a new RAG chunk

### Fallback Behavior

- If the model returns malformed JSON: treat as plain text response, no deltas, log a warning
- If delta application fails (bad path, conflicting update): skip that delta, still return response, log error
- If search follow-up fails: return the original (pre-search) response with a note that search was unavailable

### Token Budget Per Call

From spec §4.3.9:

| Component | Tokens |
|-----------|--------|
| System prompt + structured output instructions | ~500 |
| Stable context (all 5 types) | ~3,450 |
| RAG chunks | ~2,000 |
| Recent conversation | ~2,000 |
| User message | ~100–500 |
| **Input total** | **~8,000–8,500** |
| Response + deltas JSON | ~500–1,500 |
| **Total per call** | **~8,500–10,000** |

Well within Gemini Flash's 1M context window. Leaves massive headroom.

### RAG Role & Budget Rationale

> **Decision:** RAG budget reduced from ~4,000–6,000 tokens to ~2,000. Stable context is the primary memory; RAG is supplementary.

With the five stable context types (Entity Sheets, World State, Decision Log, Player Codex, Narrative Threads) capturing all *facts, decisions, and state*, RAG's only remaining job is recalling **the AI's own past advice and analysis** — the *discussion*, not the facts.

**Evidence from user study (research-protocol.md):**

| Query type | % of participants | Resolved by stable context? | Needs RAG? |
|---|---:|---|---|
| Build advice / level-up decisions | 71% | ✅ Entity Sheet (state, plan, constraints) | No |
| "Remind me about [NPC/quest/event]" | 45% | ✅ Decision Log, World State | Partially — only if asking about past *discussion* |
| "Is this good for my build?" | 39% | ✅ Entity Sheet + web search | No |
| "What would my character do?" | 34% | ✅ Philosophy, constraints, Narrative Threads | No |
| **"Summarize what happened last session"** | **31%** | ❌ | **Yes** — stable context has state *changes* but not conversation flow |
| Strategic planning | 28% | ✅ World State, Entity Sheets | No |
| **"What did we discuss about X?"** | **19%** | ❌ | **Yes** — AI's past analysis/recommendations |
| **Lore / theory crafting** | **18%** | ❌ | **Yes** — past discussion threads |

**Key findings from restart document analysis (§B.5):**
- 74% of participants omitted quest journal contents — "Player knows where they are; AI can re-derive from conversation"
- The Keth restart document is 100% stable-context-shaped data. Zero past-conversation recall.
- The restart document represents the *minimum viable context floor*. RAG sits above this floor.

**If RAG returns nothing:** User must re-ask their question or provide context again. Experience degrades but doesn't break.
**If stable context fails:** Product is useless — AI doesn't know who the player is, what they're doing, or what rules apply.

**Implementation implication for M3:** The existing bag-of-words RAG (already coded) is sufficient at this reduced budget. ~2,000 tokens ≈ 3 short recalled chunks. No need for embeddings or vector DB in v1. Can upgrade to semantic search post-launch if recall quality is insufficient.

---

## Decision Log

| # | Decision | Rationale | Date | Decided By |
|---|----------|-----------|------|------------|
| 1 | Python 3.12+ | Latest stable; needed for modern typing and performance | 2026-02-05 | Morgan |
| 2 | FastHTML + Uvicorn | Pure Python UI framework built on Starlette/ASGI. No JS build step. HTML output is what Playwright tests against — enables autonomous TDD. HTMX handles dynamic updates. | 2026-02-05 | Morgan |
| 3 | HTMX (via FastHTML) | Partial page updates, SSE streaming, form submission — all without writing JS. Produces stable, testable HTML. | 2026-02-05 | Morgan, Casey |
| 4 | SQLite via aiosqlite + raw SQL | Simple, zero-config, async-friendly. No ORM overhead for v1. | 2026-02-05 | Morgan |
| 5 | google-generativeai SDK | Official Gemini Python SDK; simplest path to structured output + streaming | 2026-02-05 | Morgan |
| 6 | pytest + playwright | pytest for all tests; playwright for browser E2E tests through the real UI | 2026-02-05 | Riley, Morgan |
| 7 | src layout with pyproject.toml | Standard Python packaging; `src/gamecompanion/` avoids import ambiguity | 2026-02-05 | Morgan |
| 8 | SSE for streaming responses | Simpler than WebSocket for unidirectional token streaming; native EventSource in browsers | 2026-02-05 | Morgan |
| 9 | API keys stored in local JSON config (encrypted at rest) | Simple for v1; can migrate to keyring later. Never served to browser. | 2026-02-05 | Morgan |
| 10 | Autonomous TDD loop: server background process → Playwright E2E → read output → fix → repeat | Framework choice must allow agent to validate UX without human in the loop. FastHTML's direct HTML output makes this possible. | 2026-02-05 | Morgan |
| 11 | **Single-call orchestration:** one LLM call returns response + context deltas + search decision as structured JSON. Optional second call only if search needed. AI's own response never triggers deltas — only user messages do. | Eliminates 2–3 calls/message overhead. See "Chat + Stable Context Orchestration" section above for full architecture. | 2026-02-05 | Morgan, Sam |
| 12 | **RAG is supplementary, not primary.** Budget reduced from ~4–6K to ~2K tokens. Stable context is the primary memory (facts, state, decisions). RAG only recalls past *conversation* (AI advice, discussion threads, session summaries). Existing bag-of-words implementation is sufficient at this budget. | User study: 31% need session summary, 19% need discussion recall, but 71%+ of top queries resolve from stable context alone. Restart docs contain zero past-conversation recall. See "RAG Role & Budget Rationale" section. | 2026-02-05 | Morgan, Sam |

---

## Action Items

| # | Action | Owner | Due | Status |
|---|--------|-------|-----|--------|
| 1 | Schedule technical design kickoff meeting | Morgan | TBD | 🔴 Not Started |
| 2 | Evaluate and select web framework | Team | TBD | 🔴 Not Started |
| 3 | Evaluate and select vector search approach | Team | TBD | 🔴 Not Started |
| 4 | Prototype M1 ("First Conversation" milestone) | Alex | TBD | 🔴 Not Started |
| 5 | Define API contract (if REST) or page routes (if server-rendered) | Team | TBD | 🔴 Not Started |
| 6 | Set up project scaffolding based on decisions | Alex | TBD | 🔴 Not Started |

---

## Participants

| Role | Name | Required |
|------|------|----------|
| Tech Lead (Staff Dev) | Morgan | ✅ |
| Junior Developer | Alex | ✅ |
| Product Owner | Jordan | Optional (for clarifications) |
| QA Lead / Tester | Riley | ✅ |
| UX Consultant | Casey | Optional |
| Spec Author (PM) | Sam | Optional |
