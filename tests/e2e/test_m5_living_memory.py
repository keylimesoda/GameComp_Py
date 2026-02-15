"""
M5: Living Memory — End-to-End Tests
====================================

Tests for Milestone 5: AI automatically tracks stable context using
structured JSON output with context_deltas, persists updates, and
lets users view/correct memory via natural language.

Spec references
---------------
- F3.4–F3.10  Structured output + stable context + corrections/pins
- §4.3.1–4.3.9 Stable context types + update mechanics
- §6.5–6.8 User flows for pin, view, update, correction
- tech-design-session.md §Orchestration (context_deltas + single-call)
- test-spec §3.5–3.10 (M5 scenarios)

Milestone acceptance criteria
-----------------------------
• Structured JSON includes context_deltas
• Deltas applied to stable context store
• "📌 Memory updated" indicator shown when deltas applied
• Users can view memory via natural language
• Users can correct memory and pin facts
• Stable context influences later responses

Test strategy
-------------
In test mode, the mock LLM emits deterministic context_deltas based on
user messages. The app applies deltas to SQLite stable context tables.
These tests validate that the memory is persisted and surfaced through
natural language queries.
"""

import re

from playwright.sync_api import Page, expect


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


# ── 1. Stable Context Auto-Update ────────────────────────────────────────


class TestStableContextAutoUpdate:
    """Auto-detection updates memory (test-spec §3.5–3.6)."""

    def test_character_sheet_created_and_viewable(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M5 Auto Update", "Baldur's Gate 3")

        _send_message(page, "My character Keth is a level 6 shadow monk with 18 DEX")

        # Memory updated indicator shown (📌 followed by summary)
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("📌", timeout=5_000)

        _send_message(page, "Show me Keth's character sheet")
        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()
        assert "Keth" in text
        assert re.search(r"level\s*6", text, re.IGNORECASE)
        assert "shadow monk" in text.lower()
        assert re.search(r"DEX\s*18", text, re.IGNORECASE)

    def test_level_up_detection(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M5 Level Up", "Baldur's Gate 3")

        _send_message(page, "Keth is a level 6 shadow monk")
        _send_message(page, "I just leveled up Keth to level 7!")

        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("📌", timeout=5_000)

        _send_message(page, "Show me Keth's character sheet")
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("level 7", timeout=5_000)


# ── 2. User Corrections ─────────────────────────────────────────────────


class TestUserCorrections:
    """User corrections update memory (test-spec §3.7)."""

    def test_correction_updates_stats(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M5 Corrections", "Baldur's Gate 3")

        _send_message(page, "Keth has 16 WIS")
        _send_message(page, "That's wrong — Keth actually has 18 WIS, not 16")

        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("📌", timeout=5_000)

        _send_message(page, "Show me Keth's stats")
        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content()
        assert re.search(r"WIS\s*18", text, re.IGNORECASE)
        assert "WIS 16" not in text


# ── 3. View Stable Context via Natural Language ─────────────────────────


class TestViewStableContext:
    """Viewing memory via natural language queries (test-spec §3.8)."""

    def test_view_party_and_world_state(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M5 View", "Baldur's Gate 3")

        _send_message(page, "Keth is a shadow monk in my party")
        _send_message(page, "We are in Act 2 at Moonrise Towers and our goal is to rescue Nightsong")

        _send_message(page, "What do you remember about my party?")
        party_text = page.get_by_test_id("ai-message").last.text_content()
        assert "Keth" in party_text

        _send_message(page, "Where am I in the story?")
        story_text = page.get_by_test_id("ai-message").last.text_content()
        assert "Act 2" in story_text
        assert "Moonrise" in story_text


# ── 4. Pin Fact to Memory ───────────────────────────────────────────────


class TestPinFact:
    """Explicit pin should persist to memory (test-spec §3.9)."""

    def test_pin_fact_then_recall(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M5 Pin", "Baldur's Gate 3")

        _send_message(page, "Remember this: Lae'zel is on probation and not fully trusted")
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("📌", timeout=5_000)

        _send_message(page, "What do you remember about Lae'zel?")
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("probation", timeout=5_000)


# ── 5. Stable Context in Responses ──────────────────────────────────────


class TestStableContextInEveryResponse:
    """Stable context influences later responses (test-spec §3.10)."""

    def test_response_uses_memory(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M5 Context", "Baldur's Gate 3")

        _send_message(page, "Keth is a shadow monk")
        _send_message(page, "We use a non-lethal approach whenever possible")

        _send_message(page, "Should I kill this goblin?")
        last_ai = page.get_by_test_id("ai-message").last
        text = last_ai.text_content().lower()
        assert "keth" in text
        assert "non-lethal" in text or "nonlethal" in text
