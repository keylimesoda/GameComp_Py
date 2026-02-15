# ⚠️ SUPERSEDED – Historical Reference Only

> **This document has been superseded as of February 6, 2026.**  
> The spec was restructured to a pure product document (v3.0), and all technical decisions are being made fresh in [tech-design-session.md](tech-design-session.md).  
> This file is retained as historical context only. Do not use these decisions as a starting point for implementation.

---

# Game Companion – Technical Spec Review v2 (Python/WebUI)

**Date:** February 5, 2026  
**Status:** ❌ Superseded by spec v3.0 product-only rewrite  
**Participants:**
- **Alex** – Junior Developer
- **Morgan** – Staff Developer (Tech Lead)
- **Jordan** – Product Owner
- **Sam** – Spec Author (Product Manager)
- **Riley** – QA Engineer *(new to review)*
- **Casey** – External UX Consultant *(new to review)*

**Documents Reviewed:** spec.md v2.0, test-spec.md v2.0

---

## Meeting Transcript

### Opening

**Sam (PM):** Welcome everyone. Quick context: we shipped a v1 spec for a .NET MAUI app with a CLI-first approach. We've since pivoted to Python with a web UI. Morgan and Alex know the history; Riley and Casey, you're seeing this fresh. That's exactly what we need – tear it apart.

**Casey (UX):** I've read both docs. I have opinions.

**Riley (QA):** Same. I have a lot of questions about testability.

**Morgan (Staff):** Good. I'll start with the Python stack decisions, then we can open it up. The v1 review covered RAG, stable context, and LLM abstraction – those concepts still hold. What changed is the *platform*, and that has ripple effects everywhere.

---

## Session 1: Python Stack & Architecture

### 1. Vector Database Choice

**Morgan (Staff):** The spec says "SQLite with vector search support" in NF3, but doesn't name a specific library. In the .NET world we chose sqlite-vss. In Python, we have much better options:

1. **ChromaDB** – embedded vector DB, Python-native, great API, supports SQLite backend
2. **FAISS** – Facebook's vector library, fastest similarity search, but no persistence built-in
3. **sqlite-vec** – the successor to sqlite-vss, maintained by Alex Garcia, pure SQLite extension
4. **NumPy cosine similarity** – roll our own with embeddings stored as BLOBs in SQLite

**Alex (Junior):** Which is simplest?

**Morgan (Staff):** ChromaDB. It handles embedding storage, similarity search, and metadata filtering in one package. We'd still use SQLite for playthroughs, messages, settings – but vector search goes through Chroma.

**Riley (QA):** Does ChromaDB support playthrough isolation? That's a major test requirement.

**Morgan (Staff):** Yes – we'd use Chroma "collections," one per playthrough. Queries are scoped to a collection by default. No cross-playthrough leakage.

**Sam (PM):** Any downsides?

**Morgan (Staff):** It adds a dependency (~50MB). And if we ever want a single-file database, we'd need to revisit. But for v1, the productivity gain is worth it.

**Jordan (PO):** I'm fine with it. Can we swap later if needed?

**Morgan (Staff):** Yes – the `LlmClient` abstraction handles embeddings. ChromaDB is an implementation detail behind our embedding service. Swappable.

> **📋 ACTION: NF3 → specify ChromaDB as vector store for v1; SQLite for relational data (playthroughs, messages, settings, stable context)**

---

### 2. SQLite ORM / Data Access

**Alex (Junior):** For the SQLite side, are we using raw `sqlite3` or an ORM?

**Morgan (Staff):** I'd recommend **SQLAlchemy** with **aiosqlite** for async support. SQLAlchemy gives us:
- Models as Python classes (type-safe, IDE-friendly)
- Migration support via Alembic (schema versioning – ties into our `schema_version` requirement)
- Connection pooling
- Easy test fixtures with in-memory databases

**Riley (QA):** In-memory databases for testing is huge. That means unit tests don't touch disk and run fast.

**Morgan (Staff):** Exactly. And we can seed test databases with fixture data.

**Alex (Junior):** Is SQLAlchemy hard to learn?

**Morgan (Staff):** The 2.0 API is actually clean. I'll pair with you on the initial models. The mapping from our spec is straightforward:

```python
class Playthrough(Base):
    __tablename__ = "playthroughs"
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str]
    game: Mapped[str]
    last_played: Mapped[datetime]

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    playthrough_id: Mapped[str] = mapped_column(ForeignKey("playthroughs.id"))
    role: Mapped[str]  # "user" | "assistant"
    content: Mapped[str]
    timestamp: Mapped[datetime]
```

> **📋 ACTION: NF3 → specify SQLAlchemy + aiosqlite for relational data access; Alembic for schema migrations**

---

### 3. API Key Storage

**Morgan (Staff):** The spec says "API keys stored in encrypted local configuration file (never exposed to browser)." That's too vague. I flagged this earlier. We need a concrete approach.

**Sam (PM):** What are the Python options?

**Morgan (Staff):** Three reasonable ones:

1. **`keyring` library** – uses OS credential store (Windows Credential Locker, macOS Keychain, Linux SecretService). Closest to the old MAUI SecureStorage approach.
2. **`cryptography.fernet`** – symmetric encryption of a local config file. We'd need a machine-derived key.
3. **`.env` file with restricted permissions** – simple, but plaintext on disk.

I recommend **`keyring`** as primary, with **Fernet-encrypted config file** as fallback for systems where keyring isn't available (headless Linux, some WSL setups).

**Casey (UX):** Does the user ever see or interact with any of this?

**Morgan (Staff):** No. They type their API key into the settings page, we store it. They never see a file or config path.

**Riley (QA):** How do we test this? We need to mock the keyring in tests.

**Morgan (Staff):** `keyring` has a built-in `keyring.backends.null.Keyring` for testing. We can also inject a mock backend.

> **📋 ACTION: NF7 → specify `keyring` library (OS credential store) as primary; Fernet-encrypted fallback; never `.env` for API keys**

---

### 4. Web Framework Details

**Morgan (Staff):** The spec says "FastAPI backend" but doesn't specify critical details:

**4a. ASGI Server**

We need **Uvicorn** as the ASGI server. The user starts the app with:
```bash
python -m gamecomp
```
Which internally runs:
```python
uvicorn.run("gamecomp.app:app", host="127.0.0.1", port=8080)
```

**Casey (UX):** Hold that thought – I have a *major* concern about server startup. I'll come back to it.

**4b. Static File Serving**

The web UI (HTML/CSS/JS) should be served by FastAPI itself using `StaticFiles` mount. No separate web server needed.

```python
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

**4c. CORS Policy**

Since the UI is served from the same origin, we don't need CORS in production. But for development (if someone runs a separate frontend dev server), we should allow `localhost` origins.

**4d. WebSocket vs. SSE for Streaming**

The spec mentions "HTTP / WebSocket" in the architecture diagram and F2.6 requires a typing indicator. We need to decide:

- **Server-Sent Events (SSE):** Simple, one-directional (server → client), works over HTTP. Good for streaming LLM responses token-by-token.
- **WebSocket:** Bidirectional, more complex, but supports real-time interaction patterns.

For v1, I recommend **SSE for chat streaming** and regular **HTTP POST for sending messages**. We don't need bidirectional communication – the user sends a message, the server streams back.

**Casey (UX):** Wait – are we streaming the response token by token? Like ChatGPT does?

**Morgan (Staff):** That's the question. The spec says "typing/thinking indicator" (F2.6), which could mean either:
- **Option A:** Show a spinner until the full response arrives, then display it all at once
- **Option B:** Stream tokens as they arrive, character by character

**Casey (UX):** Option B. It's not even close. Users now expect streaming responses. ChatGPT, Claude, Gemini web – they all stream. A 4-5 second spinner with no feedback feels broken. Streaming gives perceived performance even when actual latency is the same.

**Sam (PM):** Does Gemini support streaming?

**Morgan (Staff):** Yes – `generate_content` has a `stream=True` mode. But there's a complication: we're using structured output. Streaming structured JSON is tricky because you can't parse `context_updates` until the full response arrives.

**Alex (Junior):** So we stream the text part and handle updates at the end?

**Morgan (Staff):** Exactly. Two approaches:

1. **Stream text, then parse:** Gemini streams the response text in real-time. When streaming completes, we get the full structured output, parse `context_updates`, and apply them silently.

2. **Two-phase response:** The SSE stream sends text tokens, then a final `[DONE]` event with metadata (memory updated indicator, etc.).

I prefer approach 2. The SSE stream would look like:
```
event: token
data: {"text": "Based on your "}

event: token
data: {"text": "build, I'd recommend..."}

event: done
data: {"memory_updated": true, "updates_applied": 2}
```

**Casey (UX):** That's perfect. The UI shows text streaming in, then when the `done` event arrives, we can show the "📌 Memory updated" badge.

**Riley (QA):** How do we test streaming? Our E2E tests currently expect complete JSON responses.

**Morgan (Staff):** Good catch. We'll need two test modes:
1. **Non-streaming API endpoint** (`POST /api/chat/{pt_id}`) – returns complete JSON. Used by tests.
2. **Streaming endpoint** (`POST /api/chat/{pt_id}/stream`) – returns SSE stream. Used by the actual UI.

Both go through the same orchestrator. The streaming endpoint is just a different response wrapper.

**Riley (QA):** I like that. Tests stay simple, streaming is an output concern.

> **📋 ACTION: Add Uvicorn as ASGI server to NF2; specify `python -m gamecomp` as startup command**  
> **📋 ACTION: Add SSE streaming endpoint (`/api/chat/{pt_id}/stream`) for real-time token delivery**  
> **📋 ACTION: Keep non-streaming `POST /api/chat/{pt_id}` for testing and simple clients**  
> **📋 ACTION: Update F2.6 from "typing/thinking indicator" to "streaming response with token-by-token display"**  
> **📋 ACTION: Specify FastAPI StaticFiles for serving the web UI; no separate web server**

---

### 5. Server Startup & User Experience

**Casey (UX):** Okay, here's my major concern. Section 7.1 says "User starts the server and opens the web UI in their browser." That's *two steps* and one of them is terrifying for non-technical users. How exactly does someone "start the server"?

**Sam (PM):** We'd provide a script or executable...

**Casey (UX):** Be specific. Is the user opening a terminal? Running a Python command? Double-clicking an icon?

**Morgan (Staff):** Fair point. For v1, the target user is the creator – a technical user. But even so, we should make it as painless as possible. Options:

1. **`python -m gamecomp`** – requires Python installed, user runs from terminal
2. **PyInstaller / Nuitka** – bundle into a single `.exe` / app that launches the server and opens the browser automatically
3. **Startup script** – `start.bat` (Windows) / `start.sh` (Mac/Linux) that runs the server and opens the browser

For v1, I recommend option 3 with a path to option 2 for v1.1:

**Phase 1 (v1.0):** Ship `start.bat` / `start.sh` that:
- Checks Python is installed
- Creates/activates a virtual environment
- Installs dependencies if needed
- Starts Uvicorn
- Opens `http://localhost:8080` in the default browser

**Phase 2 (v1.1):** Bundle as a standalone executable with PyInstaller. Double-click to run.

**Casey (UX):** Phase 2 needs to be on the roadmap, not just a "maybe." But Phase 1 is acceptable for a technical early adopter.

**Jordan (PO):** Agreed. Can we add it to out-of-scope with a clear commitment?

**Sam (PM):** Yes. I'll add "Standalone executable packaging" to the out-of-scope table with "v1.1 – high priority" as the rationale.

**Casey (UX):** One more thing on startup – when the browser opens, if the server isn't ready yet, the user sees a connection error. We need a loading page that polls until the backend is ready.

**Morgan (Staff):** Easy. The static HTML can include a small script that polls `GET /api/health` every 500ms and shows "Starting up..." until it gets a 200.

> **📋 ACTION: Add startup scripts (`start.bat` / `start.sh`) to M1 deliverables**  
> **📋 ACTION: Add startup loading page that polls `/api/health` until backend is ready**  
> **📋 ACTION: Add "Standalone executable packaging (PyInstaller)" to out-of-scope as v1.1 priority**

---

### 6. Project Structure

**Alex (Junior):** What does the actual project layout look like? The spec doesn't define it.

**Morgan (Staff):** Good question. I'd propose:

```
gamecomp/
├── gamecomp/                  # Python package (backend)
│   ├── __init__.py
│   ├── __main__.py            # Entry point: python -m gamecomp
│   ├── app.py                 # FastAPI app creation
│   ├── config.py              # Settings, paths, env
│   ├── models/                # SQLAlchemy models
│   │   ├── playthrough.py
│   │   ├── message.py
│   │   └── stable_context.py
│   ├── services/              # Business logic
│   │   ├── orchestrator.py    # Chat orchestrator
│   │   ├── embedding.py       # RAG/embedding service
│   │   ├── search.py          # Tavily web search
│   │   ├── stable_context.py  # Stable context service
│   │   └── llm/
│   │       ├── base.py        # LlmClient ABC
│   │       └── gemini.py      # GeminiClient
│   ├── routers/               # FastAPI route handlers
│   │   ├── chat.py
│   │   ├── playthroughs.py
│   │   ├── context.py
│   │   ├── search.py
│   │   └── settings.py
│   └── database.py            # DB engine, session factory
├── static/                    # Web UI (HTML/CSS/JS)
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── tests/                     # pytest test suite
│   ├── conftest.py            # Shared fixtures
│   ├── test_rag.py
│   ├── test_tavily.py
│   ├── test_stable_context.py
│   ├── test_api.py
│   └── test_orchestrator.py
├── pyproject.toml             # Project metadata + dependencies
├── start.bat                  # Windows launcher
├── start.sh                   # Mac/Linux launcher
└── README.md
```

**Riley (QA):** I like the `conftest.py` for shared fixtures. That's where we'd put the in-memory database setup, mock LLM client, etc.?

**Morgan (Staff):** Exactly. Something like:

```python
@pytest.fixture
def db_session():
    """In-memory SQLite for each test."""
    engine = create_async_engine("sqlite+aiosqlite://")
    # ... create tables, yield session, teardown

@pytest.fixture
def mock_llm():
    """Mock LlmClient that returns canned responses."""
    client = AsyncMock(spec=LlmClient)
    client.chat.return_value = ChatResponse(text="Mock response", updates=[])
    return client
```

**Alex (Junior):** And dependency management – pip, poetry, or uv?

**Morgan (Staff):** **`pyproject.toml`** with **pip**. Keep it simple. Poetry adds complexity we don't need. If we find we need lockfile pinning, we add `pip-compile` or switch to `uv` later.

> **📋 ACTION: Add project structure to spec Section 6 (Architecture Overview)**  
> **📋 ACTION: Specify `pyproject.toml` + pip for dependency management in NF2**

---

## Session 2: UX Deep Dive

**Sam (PM):** Casey, let's go through your UX concerns systematically.

### 7. Chat Streaming & Response Display

**Casey (UX):** We covered streaming already – that's the biggest one. But there are related UI questions:

**7a. Markdown Rendering**

The AI responses will contain markdown – code blocks, bold, bullet lists, tables. The spec doesn't mention how these are rendered in the browser.

**Sam (PM):** Good catch. We need a markdown renderer.

**Casey (UX):** Use **marked.js** or **markdown-it** on the frontend. The AI response text should be rendered as rich HTML, not displayed as raw markdown text.

Code blocks in particular – if the AI shows a character sheet or JSON, it should be syntax-highlighted.

**Morgan (Staff):** Easy to add. We'll include `marked.js` + `highlight.js` in the static assets. The chat message component runs content through the renderer before displaying.

> **📋 ACTION: Add F2.9 – Chat messages rendered as Markdown (code blocks, bold, lists, tables) using client-side renderer**

---

### 8. Memory Update Indicator

**Casey (UX):** F3.5 says "subtle indicator when stable context is updated" and the wireframe shows "📌 Memory saved" inline in the message. I have concerns about this pattern.

If the AI updates context on, say, 40% of messages, users will get "📌 Memory updated" all the time. It becomes noise. They'll stop reading it.

**Jordan (PO):** But we want the user to know the system is learning...

**Casey (UX):** Agreed – but there's a spectrum. I'd propose a **three-tier system:**

**Tier 1 – Ambient (most common):** Small dot or subtle icon that appears next to the AI message. No text. Hover to see "2 memory updates applied." This covers routine updates (location changes, minor stat updates).

**Tier 2 – Informational (notable changes):** Compact inline badge: "📌 Updated Keth's level to 7." This covers changes the user explicitly discussed.

**Tier 3 – Confirmatory (user-initiated):** Full confirmation message when user explicitly says "Remember this" or "Update Alfira's spells." AI confirms in its response text: "Done – updated Alfira's Level 2 spells."

The current spec treats all updates the same. Differentiating by significance makes the UX much cleaner.

**Sam (PM):** I love this. It's the difference between "the system is learning" (good) and "the system won't stop talking about learning" (annoying).

**Riley (QA):** This has test implications. We need to verify which tier gets triggered for different update types.

**Morgan (Staff):** Implementation-wise, the structured output from the LLM already tells us the update type. We can map update types to tiers:
- Character sheet field change → Tier 1 (ambient)
- Level up, new party member → Tier 2 (informational)
- User said "Remember this" or "Update X" → Tier 3 (confirmatory)

> **📋 ACTION: Replace F3.5 with three-tier memory indicator system (ambient / informational / confirmatory)**

---

### 9. Dark Mode

**Casey (UX):** F2.3 says "Dark mode by default." I'd change this to "Dark mode by default with a toggle." Some users game in well-lit rooms. Some have vision accessibility needs that work better with light mode. Never force a color scheme.

**Sam (PM):** Fair. Toggle in settings, dark is default.

**Casey (UX):** And use CSS custom properties for theming, not hardcoded colors. Makes the toggle trivial and keeps the door open for custom themes later.

> **📋 ACTION: F2.3 → "Dark mode by default with light mode toggle in settings; implemented via CSS custom properties"**

---

### 10. Pin Interaction

**Casey (UX):** Section 7.5 says "User clicks pin icon on the message." Where is this icon? Is it on every message? Only on hover? Only on user messages?

**Sam (PM):** I was thinking a small pin icon on hover, on every message.

**Casey (UX):** On *every* message is too much. The primary pin flow is through natural language – "Remember this: X." The pin icon is a secondary interaction for when you want to retroactively pin something you said earlier.

I'd suggest:
- Pin icon appears **on hover** over any message (user or AI)
- Clicking it opens a small popover: "Pin this to memory?" with a text field to add a note
- The note field is pre-populated with the message content but editable

This way the user can pin "My character is a rogue" but also refine it to "Tav is a half-elf rogue who prefers stealth."

**Morgan (Staff):** That's a nice UX detail. Implementation is straightforward – clicking pin calls `POST /api/chat/{pt_id}` with a synthetic "Remember this: [message content + user note]" message that the orchestrator processes normally.

**Riley (QA):** Do we need to test the popover UI? That's a frontend interaction.

**Casey (UX):** For v1, manual QA on the popover is fine. The actual pinning logic goes through the same API path and is covered by your orchestrator tests.

> **📋 ACTION: Update pin interaction – hover-reveal icon on all messages, popover with editable note, processed as synthetic "Remember this" message**

---

### 11. First-Time Experience (FTUE)

**Casey (UX):** The first-time flow (Section 7.1) goes: welcome screen → enter API keys → create playthrough → chat. The API key step is a *wall*. Most gamers don't know what an API key is, let alone how to get one.

**Jordan (PO):** For v1, the target user is the creator, who's technical...

**Casey (UX):** Even so, we should minimize friction. My recommendations:

1. **Inline guidance:** Don't just show a text field. Show a step-by-step: "1. Go to [Google AI Studio](link). 2. Create a project. 3. Generate an API key. 4. Paste it here." With screenshots or a short GIF.

2. **Validation feedback:** When they paste the key, immediately validate it (call the Gemini API with a trivial request). Show ✅ or ❌ with a specific error message.

3. **Tavily key should be optional:** The spec requires both Gemini and Tavily keys upfront. Tavily should be optional – the app works without web search, just with reduced capability. Prompt for it later or show "Web search disabled – add a Tavily key in settings to enable."

**Sam (PM):** I agree on Tavily being optional. It's a "nice to have" enhancement, not a blocker.

**Morgan (Staff):** Easy change. The orchestrator already handles the case where Tavily isn't configured – it just skips web search.

**Riley (QA):** We need a test for "chat without Tavily key configured" – verify it still works, just without citations.

> **📋 ACTION: FTUE – Add inline instructions with links for obtaining API keys**  
> **📋 ACTION: FTUE – Validate API keys in real-time on entry (call API, show ✅/❌)**  
> **📋 ACTION: Make Tavily API key optional at setup; web search disabled until configured; prompt in settings**  
> **📋 ACTION: Add test: chat works without Tavily key (no search, no citations, still responds)**

---

### 12. Playthrough Selector

**Casey (UX):** The wireframe shows a simple list. That's fine for 3-5 playthroughs. What about 15? 30? Power gamers could accumulate a lot.

**Sam (PM):** Do we need search?

**Casey (UX):** Not for v1, but we should design for growth:
1. Show last 5 playthroughs prominently (recent section)
2. Below that, an "All Playthroughs" section with the full list
3. If the list exceeds ~10, add a simple text filter
4. Each item shows: name, game name, last played date, message count

The current wireframe doesn't show the game name separately. That's important for scanning – "which of my three BG3 runs is this?"

> **📋 ACTION: Update playthrough selector wireframe – add game name display, "Recent" section, text filter for 10+ playthroughs**

---

### 13. Accessibility

**Casey (UX):** The spec has zero accessibility mentions. For v1, we need at minimum:

1. **Keyboard navigation** – Tab through messages, Enter to send, Escape to close modals
2. **Semantic HTML** – proper heading hierarchy, ARIA labels on interactive elements
3. **Contrast ratios** – both dark and light themes need WCAG AA contrast (4.5:1 for text)
4. **Screen reader support** – chat messages should be announced, memory indicators should have aria-live regions

**Sam (PM):** All of this for v1?

**Casey (UX):** The first three are zero-cost if you build correctly from the start. They're expensive to retrofit. Screen reader polish can be v1.1 but the semantic HTML foundation has to be there now.

**Morgan (Staff):** Agreed. Using semantic HTML and ARIA labels is just... correct HTML. No extra effort.

> **📋 ACTION: Add NF8 – Accessibility: keyboard navigation, semantic HTML, WCAG AA contrast ratios; screen reader polish in v1.1**

---

### 14. Citation Display

**Casey (UX):** F4.4 says citations displayed "inline or as footnotes." That "or" needs to be a decision.

I recommend **inline with expandable details:**
- Citation appears as a superscript link: "The Nameless King is weak to lightning[¹]"
- Clicking the number shows a tooltip/popover with: source title, URL, snippet
- At the bottom of messages with citations, a collapsed "Sources" section lists all references

This is the pattern used by Perplexity and it works well for trust without clutter.

**Sam (PM):** Makes sense. Let's go with that.

> **📋 ACTION: F4.4 → specify inline superscript citations with expandable source details; collapsed "Sources" section at message bottom**

---

## Session 3: Testability & QA Strategy

**Sam (PM):** Riley, your turn. What concerns do you have?

### 15. LLM Mocking Strategy

**Riley (QA):** My biggest concern: how do we test anything that touches the LLM? Every E2E test in the test spec calls `POST /api/chat`, which ultimately calls Gemini. We can't:
- Run tests in CI without an API key
- Get deterministic results (LLM responses vary)
- Test without network access
- Run tests quickly (each LLM call is 2-5 seconds)

**Morgan (Staff):** This is the classic LLM testing problem. Here's my proposal:

**Layer 1 – Unit tests with mock LlmClient:**
The `LlmClient` ABC lets us inject a `MockLlmClient` that returns canned structured responses. This covers the orchestrator, structured output parsing, context updates – everything except the actual API call.

```python
class MockLlmClient(LlmClient):
    def __init__(self, responses: dict[str, ChatResponse]):
        self.responses = responses
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Return pre-configured response based on message content
        for trigger, response in self.responses.items():
            if trigger in request.messages[-1].content:
                return response
        return ChatResponse(text="Default mock response", updates=[])
```

**Layer 2 – API integration tests with FastAPI TestClient + mock LLM:**
FastAPI has `TestClient` which lets us test HTTP endpoints without running a server. We override the LLM dependency with our mock:

```python
@pytest.fixture
def client(mock_llm):
    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**Layer 3 – Real API smoke tests (optional, gated):**
A small suite of tests that call real Gemini/Tavily APIs. Run manually or in CI with secrets. Marked with `@pytest.mark.integration`:

```bash
# Run only unit + API mock tests (default, CI-safe)
pytest

# Run everything including real API tests
pytest --run-integration
```

**Riley (QA):** That's solid. So the 128 tests in the test spec – almost all of them run with mocks?

**Morgan (Staff):** Yes. Only 5-10 tests would need real API calls, and those are opt-in.

**Riley (QA):** I want to add one more layer: **golden file tests** for structured output parsing. We capture real Gemini responses, save them as JSON fixtures, and test our parser against them. This catches if Gemini changes its response format.

**Morgan (Staff):** Good idea. We'll add a `tests/fixtures/` directory with sample LLM responses.

> **📋 ACTION: Define three-layer test strategy in test-spec.md: (1) unit with mock LLM, (2) API with TestClient + mock, (3) optional real API smoke tests**  
> **📋 ACTION: Add `tests/fixtures/` for golden file LLM response fixtures**  
> **📋 ACTION: Add `@pytest.mark.integration` marker for real API tests; excluded from default `pytest` run**

---

### 16. Frontend Testing

**Riley (QA):** The test spec has zero frontend tests. The UI is now a first-class part of the product, not "deferred." We need at minimum:

1. **Manual QA checklist** – already exists (Section 8), that's good
2. **Automated E2E browser tests** – we should plan for Playwright in v1.1
3. **JavaScript unit tests** – if the frontend has any logic (message rendering, SSE handling, theme toggle)

For v1, I'm okay with manual QA for the UI plus automated API tests. But the test spec should *acknowledge* the gap and have a plan.

**Casey (UX):** I'd add: the SSE streaming handler in JavaScript is complex enough to deserve a unit test. If that breaks, the whole chat experience breaks.

**Morgan (Staff):** Fair. We can add a small **Jest** or **Vitest** setup for the JavaScript. Three tests:
- SSE client connects and receives tokens
- SSE client handles `done` event with metadata
- SSE client handles connection errors gracefully

**Riley (QA):** That's minimal and high-value. I'll add it to the test spec.

> **📋 ACTION: Add frontend test plan to test-spec.md: Jest/Vitest for SSE client logic; Playwright E2E in v1.1**  
> **📋 ACTION: Add 3 JavaScript unit tests for SSE streaming client**

---

### 17. Test Fixtures & Seed Data

**Riley (QA):** The E2E tests create playthroughs, add messages, index them, then query. That's a lot of setup per test. We need shared fixture data.

I want a `conftest.py` with:
- `populated_playthrough` – a playthrough with 20+ messages, indexed, with stable context
- `empty_playthrough` – just created, no messages
- `multi_playthrough` – two playthroughs for isolation tests
- `mock_gemini_responses` – canned responses for each E2E scenario

**Morgan (Staff):** Yes. Sam, can you provide your BG3 conversation exports? We talked about this in the v1 review.

**Sam (PM):** I'll create a sanitized fixture set – 30 messages covering level-ups, spell changes, party changes, and lore questions. Enough to exercise all the stable context scenarios.

**Riley (QA):** Perfect. I'll design the fixtures around those.

> **📋 ACTION: Sam to provide BG3 conversation fixture data (30 messages) for test suite**  
> **📋 ACTION: Add shared pytest fixtures to `conftest.py`: populated_playthrough, empty_playthrough, multi_playthrough, mock responses**

---

### 18. API Contract Testing

**Riley (QA):** The test spec defines API endpoints and expected results, but there's no schema validation. If `POST /api/playthroughs` returns `{"id": "abc"}` today and `{"playthrough_id": "abc"}` tomorrow, our frontend breaks.

I want **response schema validation** on every API test. FastAPI generates OpenAPI schemas automatically – we should test against them.

**Morgan (Staff):** FastAPI with Pydantic models gives us this almost for free. Every endpoint has a response model:

```python
class PlaythroughResponse(BaseModel):
    id: str
    name: str
    game: str
    last_played: datetime

@router.post("/api/playthroughs", response_model=PlaythroughResponse)
async def create_playthrough(...):
```

Pydantic validates the response shape at runtime. If the response doesn't match the model, FastAPI raises an error.

**Riley (QA):** Good – so the contract is enforced by the framework. I'll add schema validation assertions to the API tests as well, to catch any cases where we bypass the model.

> **📋 ACTION: All API endpoints must define Pydantic response models; add to spec Section 6 as architectural requirement**

---

### 19. Missing Test Coverage

**Riley (QA):** I found several gaps in the test spec:

| Gap | Risk | Recommendation |
|-----|------|----------------|
| No test for chat without Tavily key | User can't chat if Tavily fails? | Add E2E test: chat works with search disabled |
| No test for concurrent requests | DB corruption under load | Add test: 5 simultaneous chat requests to same playthrough |
| No test for large playthrough import | Import could timeout or OOM | Add test: import 500-message playthrough |
| No test for SSE stream interruption | User closes browser mid-stream | Add test: verify server handles client disconnect |
| No test for database migration | Schema upgrade breaks existing data | Add test: v1 DB loads after v2 schema migration |
| No negative API tests | Malformed requests could crash server | Add tests: wrong content-type, missing fields, invalid IDs |

**Morgan (Staff):** All valid. The concurrent requests one is important – SQLite has a single-writer lock. We need to verify aiosqlite handles that gracefully.

**Alex (Junior):** What happens if two chat requests hit at the same time?

**Morgan (Staff):** SQLite queues writes with WAL mode. It won't corrupt, but the second request might wait. We should test that the wait time is reasonable and no request is dropped.

**Riley (QA):** I'll add all six to the test spec as Section 6.3, "Infrastructure & Reliability Tests."

> **📋 ACTION: Add 6 new test categories to test-spec.md: chat-without-search, concurrency, large import, stream disconnect, DB migration, negative API tests**

---

## Session 4: Final Review & Remaining Issues

### 20. Milestone Re-estimation

**Jordan (PO):** The milestones kept the same estimates from the .NET version. Are those still accurate?

**Morgan (Staff):** Mostly, but some shifts:

| Milestone | .NET Estimate | Python Estimate | Reason |
|-----------|--------------|-----------------|--------|
| M1 – Scaffolding + Chat + Gemini | 1 week | 1 week | Faster in Python, but web UI adds work |
| M2 – Playthrough management | 1 week | 1 week | Same complexity |
| M3 – SQLite storage | 1 week | 0.5 weeks | SQLAlchemy is faster than EF Core setup |
| M4 – RAG | 2 weeks | 1.5 weeks | ChromaDB does heavy lifting vs. raw sqlite-vss |
| M5 – Web search | 1 week | 1 week | Same |
| M6 – Stable context | 1 week | 1 week | Same |
| M7 – Context-aware chat | 1 week | 1 week | Same |
| M8 – Settings + UI flows | 1 week | 1.5 weeks | Web UI polish takes more work than CLI |
| M9 – Testing + polish | 1 week | 1.5 weeks | More surface area with web UI |

**Net:** About the same. Some milestones are faster, some slower. Still ~10 weeks.

**Casey (UX):** I'd push back on M8 and M9. The web UI needs design iteration. Can we front-load the UI layout into M1 instead of leaving all polish to the end?

**Morgan (Staff):** Good point. M1 should deliver a working (if rough) chat UI. We iterate on it throughout. M8 and M9 refine, not create from scratch.

**Sam (PM):** Let me update M1's deliverable to make that explicit.

> **📋 ACTION: Update M1 deliverable to include "functional (rough) web UI with chat, playthrough selector, settings stub"**  
> **📋 ACTION: Update M3 estimate to 0.5 weeks; M8 to 1.5 weeks; M9 to 1.5 weeks (total stays ~10 weeks)**

---

### 21. Dependency Management & Pinning

**Morgan (Staff):** One more thing – we need to specify our Python version and key dependencies:

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | ≥3.11 | Target runtime |
| FastAPI | ≥0.109 | Web framework |
| Uvicorn | ≥0.27 | ASGI server |
| SQLAlchemy | ≥2.0 | ORM |
| aiosqlite | ≥0.20 | Async SQLite driver |
| chromadb | ≥0.4 | Vector database |
| google-generativeai | ≥0.4 | Gemini API client |
| keyring | ≥25.0 | Secure credential storage |
| cryptography | ≥42.0 | Fernet encryption fallback |
| pydantic | ≥2.0 | Data validation (comes with FastAPI) |
| httpx | ≥0.27 | HTTP client for Tavily/external APIs |
| pytest | ≥8.0 | Test framework |
| pytest-asyncio | ≥0.23 | Async test support |

**Riley (QA):** Add `pytest-httpx` for mocking HTTP calls in tests. And `factory-boy` for generating test fixtures.

**Morgan (Staff):** Good additions.

> **📋 ACTION: Add dependency table to spec Section 6 or NF2**

---

### 22. Local Security Model

**Morgan (Staff):** Last technical concern. The web app runs on `localhost:8080`. We need to ensure:

1. **Bind to 127.0.0.1 only** – not `0.0.0.0`. No external access.
2. **No authentication required** – it's a local-only app. Adding auth would be over-engineering.
3. **API keys never sent to the browser** – the frontend never sees raw keys. Settings page shows masked values ("gemini-key: ****abc").
4. **CORS disabled in production** – same-origin only.

**Riley (QA):** Add a test: verify the server only binds to localhost. And a test: verify `GET /api/settings` doesn't return raw API keys.

**Morgan (Staff):** The API key masking should be in the Pydantic response model. The `Settings` model simply never serializes the full key:

```python
class SettingsResponse(BaseModel):
    gemini_key_configured: bool
    gemini_key_hint: str  # "****abc" – last 3 chars only
    tavily_key_configured: bool
    tavily_key_hint: str
```

> **📋 ACTION: Add security requirements: bind to 127.0.0.1 only, no auth (local app), API keys masked in all API responses**  
> **📋 ACTION: Add tests: server binds localhost-only; settings endpoint never exposes raw keys**

---

### 23. Error Page Design

**Casey (UX):** F2.8 describes error handling for API errors, but there's no design for error *pages.* What does the user see when:
- Server isn't running (browser shows connection refused)
- Server crashes mid-session
- Backend returns 500

We need a consistent error component in the UI, not just `alert()` calls.

**Sam (PM):** What do you recommend?

**Casey (UX):** A **toast notification system** for transient errors (rate limits, network blips) and a **full-page error state** for fatal errors (server down, DB corrupted):

- **Toast:** Appears top-right, auto-dismisses after 8s, has a "Details" expand link. Used for: rate limits, Tavily failures, malformed LLM responses.
- **Full-page error:** Shows centered message with retry button and troubleshooting steps. Used for: server unreachable, database errors.
- **Inline error:** Appears in the chat as a system message. Used for: individual chat request failures.

**Riley (QA):** I'll add test scenarios for each error type and verify the correct error component is shown.

> **📋 ACTION: Add error UI design to spec Section 8: toast notifications, full-page error state, inline chat errors**

---

## Summary of All Spec Updates Required

| # | Section | Change | Owner |
|---|---------|--------|-------|
| 1 | NF3 | ChromaDB as vector store; SQLite for relational data | Morgan |
| 2 | NF2 / NF3 | SQLAlchemy + aiosqlite for data access; Alembic for migrations | Morgan |
| 3 | NF7 | `keyring` library for API key storage; Fernet fallback | Morgan |
| 4 | NF2 | Uvicorn as ASGI server; `python -m gamecomp` startup | Morgan |
| 5 | New: F2.10 | SSE streaming endpoint for token-by-token response delivery | Morgan |
| 6 | F2.6 | Update from "typing indicator" to "streaming response display" | Sam |
| 7 | NF2 | FastAPI StaticFiles for serving web UI | Morgan |
| 8 | M1 | Add startup scripts (`start.bat` / `start.sh`) | Sam |
| 9 | New | Startup loading page that polls `/api/health` | Alex |
| 10 | Out of Scope | Add "Standalone executable (PyInstaller)" as v1.1 priority | Sam |
| 11 | Section 6 | Add project structure layout | Morgan |
| 12 | NF2 | `pyproject.toml` + pip for dependency management | Morgan |
| 13 | New: F2.9 | Markdown rendering in chat messages (marked.js + highlight.js) | Casey |
| 14 | F3.5 | Three-tier memory indicator (ambient / informational / confirmatory) | Casey |
| 15 | F2.3 | Dark mode default with light mode toggle; CSS custom properties | Casey |
| 16 | F3.6 / 7.5 | Pin interaction: hover icon, popover with editable note | Casey |
| 17 | 7.1 | FTUE: inline API key instructions with links and screenshots | Casey |
| 18 | 7.1 | Real-time API key validation on entry (✅/❌) | Morgan |
| 19 | Various | Tavily API key optional at setup; web search degrades gracefully | Sam |
| 20 | 8 (wireframes) | Playthrough selector: game name, "Recent" section, text filter | Casey |
| 21 | New: NF8 | Accessibility: keyboard nav, semantic HTML, WCAG AA contrast | Casey |
| 22 | F4.4 | Inline superscript citations with expandable source details | Casey |
| 23 | 12 / test-spec | Three-layer test strategy: mock unit, TestClient API, opt-in real API | Riley |
| 24 | test-spec | `tests/fixtures/` for golden file LLM response fixtures | Riley |
| 25 | test-spec | `@pytest.mark.integration` for real API tests | Riley |
| 26 | test-spec | Frontend test plan: Jest/Vitest for SSE client; Playwright in v1.1 | Riley |
| 27 | test-spec | 3 JavaScript unit tests for SSE streaming client | Riley |
| 28 | test-spec | Shared pytest fixtures in conftest.py | Riley |
| 29 | Section 6 | All API endpoints must define Pydantic response models | Morgan |
| 30 | test-spec | 6 new test categories (concurrency, negative API, etc.) | Riley |
| 31 | M1 | Deliverable includes functional (rough) web UI | Sam |
| 32 | Milestones | M3 → 0.5 weeks; M8 → 1.5 weeks; M9 → 1.5 weeks | Sam |
| 33 | Section 6 / NF2 | Python dependency table with version requirements | Morgan |
| 34 | NF7 / New | Security: localhost-only binding, no auth, API keys masked | Morgan |
| 35 | Section 8 | Error UI: toast notifications, full-page error state, inline chat errors | Casey |
| 36 | test-spec | Tests for localhost binding and API key masking | Riley |
| 37 | test-spec | Test: chat works without Tavily key configured | Riley |
| 38 | test-spec | Sam provides BG3 fixture data (30 messages) | Sam |

---

## Sign-Off (Conditional)

After Session 4, participants indicated conditional sign-off pending spec updates:

| Role | Name | Status | Condition |
|------|------|--------|-----------|
| Staff Developer | Morgan | ⏳ Conditional | Apply actions 1–4, 7, 11–12, 18, 29, 33–34 |
| Junior Developer | Alex | ⏳ Conditional | Apply action 11 (project structure) – needs clarity to start M1 |
| Product Owner | Jordan | ⏳ Conditional | Apply actions 10, 19, 31–32 (scope, milestones) |
| Spec Author (PM) | Sam | ⏳ Conditional | Will apply all updates; needs 1 day |
| QA Engineer | Riley | ⏳ Conditional | Apply actions 23–28, 30, 36–38 to test-spec |
| UX Consultant | Casey | ⏳ Conditional | Apply actions 13–17, 20–22, 35 |

**Sam (PM):** I'll update both spec.md and test-spec.md with all 38 actions. We'll reconvene for final sign-off tomorrow.

---

## Follow-Up Meeting (February 6, 2026)

**Sam (PM):** Spec v2.1 and test-spec v2.1 are updated with all 38 actions from yesterday. I'll walk through the key changes, then we'll do individual sign-off.

### Verification Walkthrough

**Morgan (Staff):** I've reviewed the technical updates. ChromaDB in NF3, SQLAlchemy in NF2, keyring in NF7, Uvicorn, project structure, dependency table, Pydantic response models, security requirements – all present and correctly specified. One small addition: we should also specify **WAL mode** for SQLite to handle concurrent reads during chat:

```python
# In database.py initialization
engine = create_async_engine(
    "sqlite+aiosqlite:///gamecomp.db",
    connect_args={"check_same_thread": False},
)
# Enable WAL mode on first connection
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

**Sam (PM):** Added.

> **📋 ACTION: Add SQLite WAL mode to NF3 / database configuration**

---

**Casey (UX):** I've reviewed the UX updates. Markdown rendering (F2.9), three-tier memory indicator (F3.5), dark mode toggle (F2.3), pin popover (F3.6/7.5), FTUE improvements (7.1), playthrough selector (wireframe), accessibility (NF8), citation design (F4.4), error UI (Section 8) – all present.

One addition I want to flag: the **chat input area** needs a specification. Right now the wireframe shows `[Type a message...] [→]`. We need:

- **Multi-line input** – Shift+Enter for new lines, Enter to send
- **Character counter** – subtle count when approaching max length
- **Send button state** – disabled when input is empty or while response is streaming
- **Input preserved on error** – if send fails, the message stays in the input field

**Sam (PM):** Added as F2.10 (I'll renumber the SSE streaming to F2.11).

> **📋 ACTION: Add F2.10 – Chat input: multi-line (Shift+Enter), character counter, smart send button state, preserve on error**

---

**Riley (QA):** I've reviewed the test-spec updates. Three-layer test strategy, fixtures directory, integration marker, frontend test plan, shared conftest fixtures, six new test categories, Tavily-optional test, fixture data from Sam – all present.

I have two additions:

1. **Test naming convention:** All test functions must start with `test_` and use descriptive snake_case names that include the scenario and expected outcome. Example: `test_chat_without_tavily_key_returns_response_without_citations`. This is already the pattern, but let's make it explicit in the test spec.

2. **Coverage target:** For v1, I want **≥80% line coverage** on the `gamecomp/services/` directory (orchestrator, embedding, search, stable context). The routers and models are lower risk. We track coverage with `pytest-cov`.

**Morgan (Staff):** 80% on services is reasonable. The orchestrator alone is probably 40% of the codebase logic.

**Sam (PM):** Added.

> **📋 ACTION: Add test naming convention to test-spec Section 1**  
> **📋 ACTION: Add coverage target: ≥80% on `gamecomp/services/`; tracked via `pytest-cov`**

---

**Alex (Junior):** I'm good. The project structure is clear, the dependency list makes sense, and I know where to start with M1. One question: should the `static/` directory use vanilla JS or a lightweight framework?

**Morgan (Staff):** For v1, **vanilla JS** with **Web Components** if needed. No build step, no npm, no bundler. The UI is simple enough – chat messages, a sidebar, settings modal. We don't need React for that.

**Casey (UX):** Agreed. A single `app.js` with module imports keeps it simple. If it outgrows vanilla JS, we can add a lightweight framework (Alpine.js, htmx) in v2 – but I doubt we'll need it for v1.

**Alex (Junior):** Makes sense. No build step means faster iteration.

> **📋 ACTION: Specify vanilla JS (no framework, no build step) for frontend in NF2; re-evaluate in v2 if needed**

---

**Jordan (PO):** I'm satisfied. The milestones are updated, the scope is clear, the out-of-scope items have clear rationale and timeline. One request: can we add a **"Definition of Done" for each milestone**? Just a bullet list of what "complete" means so there's no ambiguity.

**Morgan (Staff):** That's a good practice. For each milestone, we list:
- Functional requirements covered
- Tests passing
- Any demo/review checkpoint

**Sam (PM):** I'll add a DoD subsection to each milestone.

> **📋 ACTION: Add "Definition of Done" checklist to each milestone in Section 13**

---

### Final Sign-Off

| Role | Name | Status | Notes |
|------|------|--------|-------|
| Staff Developer | Morgan | ✅ **Approved** | All tech decisions specified; WAL mode added |
| Junior Developer | Alex | ✅ **Approved** | Clear project structure; ready for M1 |
| Product Owner | Jordan | ✅ **Approved** | Milestones, scope, and DoD all clear |
| Spec Author (PM) | Sam | ✅ **Approved** | All 41 actions applied; spec v2.1 complete |
| QA Engineer | Riley | ✅ **Approved** | Test strategy comprehensive; coverage targets set |
| UX Consultant | Casey | ✅ **Approved** | UX foundations solid; streaming and FTUE addressed |

---

## Appendix: Additional Actions from Follow-Up

| # | Change | Owner |
|---|--------|-------|
| 39 | SQLite WAL mode for concurrent read support | Morgan |
| 40 | F2.10 – Chat input: multi-line, character counter, send button state, preserve on error | Casey |
| 41 | Test naming convention documented in test-spec | Riley |
| 42 | Coverage target ≥80% on services; `pytest-cov` | Riley |
| 43 | Vanilla JS frontend, no build step | Morgan |
| 44 | Definition of Done for each milestone | Sam/Jordan |

**Total actions: 44**

---

## Next Steps

1. **Sam** finalizes spec.md v2.1 and test-spec.md v2.1 with all 44 actions
2. **Morgan** begins technical architecture diagram for Python stack
3. **Alex** starts M1: project scaffolding, FastAPI app, basic web UI shell, Gemini integration
4. **Riley** begins setting up `conftest.py` with fixtures and mock infrastructure
5. **Casey** delivers lightweight UX mockups for chat view, playthrough selector, FTUE flow, and error states
6. **Team** reconvenes for M1 sprint planning (February 7)

---

*Review complete. All participants signed off at 100% confidence.*
