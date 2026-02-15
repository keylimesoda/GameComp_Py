"""
M3: Memory Recall — End-to-End Tests
=====================================

Tests for Milestone 3: AI recalls relevant past context via vector
similarity search (RAG) so users don't have to re-explain previously
discussed topics.

Spec references
---------------
- F3.1  Conversations stored locally per playthrough
- F3.2  Relevant past context retrieved via vector similarity search
- F3.3  Retrieved context injected into LLM prompt automatically
- §4.3    Persistent Memory (RAG) — introduction
- §4.3.9  Context Budget (RAG: ~2K tokens, recent: ~2K tokens)
- §6.2    Returning User (context recalled on reopen)
- §6.4    Typical Chat Interaction (step 2a: context recall)
- test-spec §3.2  Memory Recall Across Sessions

Milestone acceptance criteria
-----------------------------
• Past conversation context is automatically recalled during chat
• User doesn't have to re-explain previously discussed topics
• Recalled context is relevant (not random old messages)

Test strategy
-------------
The system uses a "recent window" for the last N messages and RAG for
older messages.  To test RAG recall, we:

1. Establish a distinctive fact via the UI
2. Inject enough filler messages (via /test/inject-messages) to push
   the fact outside the recent window
3. Ask about the fact — RAG retrieves it, the mock LLM echoes the
   retrieved context, and the test verifies the response contains it

In test mode the mock LLM behaves as follows:
- When RAG-retrieved context is provided  → echoes the context text
  so E2E assertions can verify recall through the visible response.
- When no RAG context is provided (short conversations within the
  recent window) → returns the original canned response.

data-testid contracts (re-uses M1/M2; no new testids for M3)
-------------------------------------------------------------
Existing: chat-container, message-input, send-btn, ai-message,
          user-message, sidebar-toggle, playthrough-sidebar,
          playthrough-item, new-playthrough-btn

Test-only endpoints introduced
-------------------------------
POST /test/inject-messages  — seed messages into DB + RAG index
GET  /test/rag-stats        — return RAG index statistics per playthrough
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
    """Send a chat message and wait for a NEW AI response.

    Uses count-based waiting so it works even when the page already
    has messages from injected filler.
    """
    page.wait_for_load_state("networkidle")
    ai_count = page.get_by_test_id("ai-message").count()
    page.get_by_test_id("message-input").fill(text)
    page.get_by_test_id("send-btn").click()
    # Wait for exactly one new AI message to appear
    expect(page.get_by_test_id("ai-message")).to_have_count(
        ai_count + 1, timeout=30_000
    )


def _get_playthrough_id(page: Page) -> int:
    """Extract playthrough ID from the current URL (/chat/{id})."""
    match = re.search(r"/chat/(\d+)", page.url)
    assert match, f"Not on a chat page: {page.url}"
    return int(match.group(1))


def _inject_filler(app_url: str, playthrough_id: int, count: int = 12):
    """Inject filler message pairs (user + assistant) into DB + RAG index.

    The filler content is deliberately unrelated to character builds,
    combat, or story progression so it won't pollute relevance tests.
    Each call injects ``count`` pairs = ``count * 2`` total messages.
    """
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


def _open_sidebar(page: Page):
    """Open the playthrough sidebar."""
    page.get_by_test_id("sidebar-toggle").click()
    expect(page.get_by_test_id("playthrough-sidebar")).to_be_visible(timeout=3_000)


# ── 1. Core RAG Recall ───────────────────────────────────────────────────


class TestContextRecall:
    """AI recalls relevant past context via RAG (F3.2, F3.3, test-spec §3.2)."""

    def test_recalls_fact_pushed_out_of_recent_window(
        self, page: Page, app_url: str
    ):
        """A distinctive fact is recalled via RAG after filler pushes it
        out of the recent conversation window."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "RAG Recall", "Baldur's Gate 3")

        # Establish a distinctive fact
        _send_message(
            page, "My character Keth is a level 6 shadow monk with 18 DEX"
        )

        # Inject filler to push the fact out of the recent window
        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=12)

        # Reload so the page reflects the full conversation
        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        # Ask about the fact — RAG should retrieve the old message
        _send_message(page, "What class is my character and what are their stats?")

        # The mock LLM echoes retrieved RAG context — verify it contains our fact
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("shadow monk", timeout=5_000)

    def test_recalls_fact_after_page_reload(self, page: Page, app_url: str):
        """RAG index persists across page reloads — simulates closing
        and reopening the browser (§6.2, test-spec §3.2)."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Persistence", "Elden Ring")

        _send_message(
            page,
            "I'm playing a faith/strength build with the Blasphemous Blade",
        )

        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=12)

        # Simulate session restart
        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        _send_message(page, "What weapon am I using in my build?")

        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("Blasphemous Blade", timeout=5_000)

    def test_relevant_context_prioritized(self, page: Page, app_url: str):
        """RAG retrieves context relevant to the query, not random old
        messages (acceptance criteria: 'relevant, not random')."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Relevance", "Baldur's Gate 3")

        # Two distinct facts about different topics
        _send_message(
            page,
            "My character Keth is a shadow monk who specializes in stealth",
        )
        _send_message(
            page,
            "The party is currently in Act 2 at Moonrise Towers fighting undead",
        )

        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=12)

        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        # Ask specifically about character class — should retrieve the monk fact
        _send_message(
            page, "Remind me about my character's class and combat style"
        )

        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("shadow monk", timeout=5_000)

    def test_recalls_multiple_related_facts(self, page: Page, app_url: str):
        """Multiple relevant facts about the same topic are recalled
        together when the query spans all of them."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Multi-Fact", "Baldur's Gate 3")

        _send_message(page, "Keth is a level 6 shadow monk")
        _send_message(page, "Keth has 18 DEX and 16 WIS as primary stats")
        _send_message(
            page,
            "Keth's build plan is to multiclass into Paladin at level 7",
        )

        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=12)

        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        _send_message(page, "Tell me everything about Keth's build plan")

        last_ai = page.get_by_test_id("ai-message").last
        # Should recall at least the class and the multiclass plan
        expect(last_ai).to_contain_text("shadow monk", timeout=5_000)
        expect(last_ai).to_contain_text("Paladin", timeout=5_000)


# ── 2. Playthrough Isolation ─────────────────────────────────────────────


class TestPlaythroughIsolation:
    """RAG respects playthrough boundaries — no cross-contamination (F1.5)."""

    def test_rag_does_not_cross_playthroughs(self, page: Page, app_url: str):
        """A fact indexed in playthrough A is never retrieved in
        playthrough B, even when the query is directly relevant."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Playthrough A", "Baldur's Gate 3")

        # Establish a distinctive fact in PT-A
        _send_message(
            page,
            "My character Shadowheart is a Trickery Domain cleric",
        )

        pid_a = _get_playthrough_id(page)
        _inject_filler(app_url, pid_a, count=12)

        # Create PT-B via sidebar
        _open_sidebar(page)
        page.get_by_test_id("new-playthrough-btn").click()
        expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
            timeout=5_000
        )
        _create_playthrough(page, "Playthrough B", "Elden Ring")

        # Ask about a cleric in PT-B — should NOT recall PT-A's data
        _send_message(page, "Do I have any cleric characters in my party?")

        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()
        assert "Shadowheart" not in text, (
            f"Cross-playthrough leak: 'Shadowheart' found in PT-B response"
        )
        assert "Trickery Domain" not in text, (
            f"Cross-playthrough leak: 'Trickery Domain' found in PT-B response"
        )


# ── 3. Long Conversation Stability ───────────────────────────────────────


class TestLongConversationStability:
    """System handles long conversations within context budget (§4.3.6)."""

    def test_chat_works_after_many_messages(self, page: Page, app_url: str):
        """Chat remains functional after 30+ messages — no token
        overflow or crashes."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Stress Test", "Elden Ring")

        _send_message(page, "Starting a long playthrough conversation")

        pid = _get_playthrough_id(page)
        _inject_filler(app_url, pid, count=30)

        page.reload()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        # Send a new message — should get a response without errors
        _send_message(page, "Are you still there after all that?")
        expect(page.get_by_test_id("ai-message").last).to_be_visible(
            timeout=30_000
        )


# ── 4. RAG Infrastructure ────────────────────────────────────────────────


class TestRagInfrastructure:
    """Verify RAG indexing via test-only endpoints."""

    def test_messages_indexed_after_send(self, page: Page, app_url: str):
        """After sending messages through the UI, the RAG index contains
        the expected entries."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Index Test")

        _send_message(page, "Testing that RAG indexing works")

        pid = _get_playthrough_id(page)
        resp = httpx.get(
            f"{app_url}/test/rag-stats",
            params={"playthrough_id": str(pid)},
            timeout=5.0,
        )
        assert resp.status_code == 200
        stats = resp.json()
        # At least 2 entries: the user message + the AI response
        assert stats["indexed_count"] >= 2, (
            f"Expected ≥2 indexed messages, got {stats['indexed_count']}"
        )
