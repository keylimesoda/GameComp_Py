"""
M4: Web Search & Citations — End-to-End Tests
===============================================

Tests for Milestone 4: LLM decides when web search is needed via
structured JSON output, orchestrator executes search via Tavily,
and responses include numbered citations with source URLs.

Spec references
---------------
- F4.1  Web search access (Tavily)
- F4.2  LLM decides search via structured JSON; orchestrator executes
- F4.3  All external information cited with source URLs
- F4.4  Citations displayed inline or as footnotes, numbered [1], [2]…
- F4.5  Introduces { response, web_search } structured JSON format
- test-spec §3.3  Web Search with Citations scenario
- tech-design-session.md §Orchestration (single-call + optional search)

Milestone acceptance criteria
-----------------------------
• Game-specific queries trigger web search with cited results
• Non-game queries (greetings, recall) do NOT trigger search
• Citations use numbered [1], [2] format with source URLs
• Structured JSON output format: { response, web_search }
• Fallback: malformed JSON treated as plain-text response

Test strategy
-------------
In test mode the app uses mock services:

  Mock LLM (first call):
    – Detects game-specific keywords ("beat", "defeat", "boss"…)
      → returns JSON with web_search populated
    – Non-game messages → returns JSON with web_search: null
    – RAG context provided → echoes context, web_search: null

  Mock Tavily:
    – Returns 2 canned search results with known URLs

  Mock LLM (second call, with search results):
    – Returns response text with [1], [2] citations and source URLs

The test verifies user-visible outcomes: citations, URLs, and
non-citation responses where appropriate.

data-testid contracts (re-uses M1–M3; no new testids for M4)
-------------------------------------------------------------
Existing: chat-container, message-input, send-btn, ai-message,
          user-message, api-key-input, save-key-btn,
          create-playthrough-heading, playthrough-name-input,
          game-title-input, create-playthrough-btn
"""

import re
import json

from playwright.sync_api import Page, expect
import httpx


# ── Helpers ───────────────────────────────────────────────────────────────


def _setup_with_key(page: Page, app_url: str):
    """Enter API key and land on playthrough creation screen."""
    page.goto(app_url)
    page.get_by_test_id("api-key-input").fill("test-key-valid")
    page.get_by_test_id("save-key-btn").click()
    expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
        timeout=5_000
    )


def _create_playthrough(page: Page, name: str, game_title: str = ""):
    """Create a playthrough from the creation screen."""
    page.get_by_test_id("playthrough-name-input").fill(name)
    if game_title:
        page.get_by_test_id("game-title-input").fill(game_title)
    page.get_by_test_id("create-playthrough-btn").click()
    expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)


def _send_message(page: Page, text: str):
    """Send a chat message and wait for a NEW AI response."""
    page.wait_for_load_state("networkidle")
    ai_count = page.get_by_test_id("ai-message").count()
    page.get_by_test_id("message-input").fill(text)
    page.get_by_test_id("send-btn").click()
    expect(page.get_by_test_id("ai-message")).to_have_count(
        ai_count + 1, timeout=30_000
    )


def _get_playthrough_id(page: Page) -> int:
    """Extract playthrough ID from the current URL (/chat/{id})."""
    match = re.search(r"/chat/(\d+)", page.url)
    assert match, f"Not on a chat page: {page.url}"
    return int(match.group(1))


def _inject_filler(app_url: str, playthrough_id: int, count: int = 12):
    """Inject filler message pairs to push facts out of the recent window."""
    messages = []
    topics = [
        "game UI settings and key bindings",
        "save file management and backup tips",
        "planning next gaming session schedule",
        "game soundtrack and audio design",
        "graphical settings and frame rate tuning",
        "controller versus keyboard debate",
        "photo mode tips and screenshots",
        "loading screen trivia and lore tidbits",
        "comparing editions and DLC bundles",
        "community mod recommendations",
        "achievement hunting strategies",
        "patch notes and version history",
    ]
    for i in range(count):
        topic = topics[i % len(topics)]
        messages.append(
            {"role": "user", "content": f"Let's talk about {topic} ({i})"}
        )
        messages.append(
            {"role": "assistant", "content": f"Sure! Here's info about {topic} ({i})."}
        )
    resp = httpx.post(
        f"{app_url}/test/inject-messages",
        data={
            "playthrough_id": str(playthrough_id),
            "messages": json.dumps(messages),
        },
        timeout=10.0,
    )
    assert resp.status_code == 200, f"Inject failed: {resp.status_code} {resp.text}"


# ── 1. Core Web Search with Citations ────────────────────────────────────


class TestWebSearchCitations:
    """AI searches the web and cites sources (F4.1–F4.4, test-spec §3.3)."""

    def test_game_query_returns_response_with_citations(
        self, page: Page, app_url: str
    ):
        """Game-specific query triggers web search; response includes
        numbered citations and source URLs (test-spec §3.3 full scenario)."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Elden Ring Run", "Elden Ring")

        _send_message(page, "How do I beat Margit in Elden Ring?")

        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()

        # Response should have substantive advice (not just "let me search")
        assert len(text) > 50, f"Response too short for game advice: {text}"
        # Should have at least one numbered citation [1]
        citations = re.findall(r"\[\d+\]", text)
        assert len(citations) >= 1, f"No citations found in response: {text}"
        assert "[1]" in text, f"Expected citation [1] in response: {text}"

    def test_citations_use_numbered_format(self, page: Page, app_url: str):
        """Citations are numbered [1], [2], etc. as inline references
        or footnotes (F4.4)."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Citation Format", "Dark Souls 3")

        _send_message(page, "What is the best strategy to defeat the Nameless King boss?")

        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()

        # Extract citation numbers
        citation_numbers = re.findall(r"\[(\d+)\]", text)
        assert len(citation_numbers) >= 1, (
            f"No numbered citations [N] found in: {text}"
        )
        # First citation should be [1]
        assert "1" in citation_numbers, (
            f"Citations should include [1], found: {citation_numbers}"
        )

    def test_source_urls_present_in_response(self, page: Page, app_url: str):
        """Response includes at least one source URL (F4.3)."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "URL Check", "Elden Ring")

        _send_message(page, "How do I defeat the boss Godrick in Elden Ring?")

        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()

        # Check for URL pattern in the text content
        urls = re.findall(r"https?://\S+", text)
        assert len(urls) >= 1, f"No source URLs found in response: {text}"


# ── 2. Non-Game Queries (No Search) ──────────────────────────────────────


class TestNoSearchForNonGameQueries:
    """Non-game queries do NOT trigger web search (F4.2)."""

    def test_greeting_has_no_citations(self, page: Page, app_url: str):
        """A simple greeting should not trigger web search or include
        citation markers."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "No Search Chat")

        _send_message(page, "Hello there, how are you today?")

        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()

        # Should NOT have numbered citation markers
        citations = re.findall(r"\[\d+\]", text)
        assert len(citations) == 0, (
            f"Unexpected citations in greeting response: {text}"
        )

    def test_recall_query_has_no_citations(self, page: Page, app_url: str):
        """A memory-recall query (referencing past conversation) should
        use RAG, not web search, and have no citation markers."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Recall No Search", "Baldur's Gate 3")

        # Establish a fact and push it out of recent window
        _send_message(
            page, "My character Valeria is a level 8 paladin with 18 STR"
        )
        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=12)

        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        # Ask about the fact — should recall via RAG, not search
        _send_message(page, "Tell me about Valeria's class and level")

        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()

        # Should recall the fact (RAG)
        assert "paladin" in text.lower(), (
            f"Expected RAG recall of 'paladin' in response: {text}"
        )
        # Should NOT have web search citations
        citations = re.findall(r"\[\d+\]", text)
        assert len(citations) == 0, (
            f"Unexpected citations in recall response: {text}"
        )


# ── 3. RAG Regression ────────────────────────────────────────────────────


class TestRagRegressionWithStructuredOutput:
    """RAG recall still works correctly after M4's structured output
    transition (verifies M3 compatibility)."""

    def test_rag_recall_works_with_structured_output(
        self, page: Page, app_url: str
    ):
        """Facts pushed out of the recent window are still recalled via
        RAG through the new M4 structured-output orchestrator."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "RAG + M4", "Baldur's Gate 3")

        # Establish a distinctive fact
        _send_message(
            page, "My character Zephyr is a storm sorcerer with 20 CHA"
        )

        # Push it out of the recent window
        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=12)

        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        # Ask about the fact — RAG should retrieve it
        _send_message(page, "What do you remember about Zephyr's class and charisma?")

        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("storm sorcerer", timeout=5_000)
