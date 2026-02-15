"""
M1: First Conversation — End-to-End Tests
==========================================

Tests for Milestone 1, which delivers the first complete user experience slice:
a new user can set up the app, create a playthrough, and have their first AI
conversation.

Spec references
---------------
- Milestone M1 acceptance criteria              (spec.md §12)
- User Flow 6.1: First-Time Setup               (spec.md §6.1)
- E2E Scenario 3.1: First Conversation          (test-spec.md §3.1)
- F1.1  Create playthrough (name + game title)
- F2.1  Minimal chat UI
- F2.3  Dark mode by default
- F2.5  Chat history persists across refreshes
- F2.6  Typing/thinking indicator
- F5.1  Gemini as default model (mocked in tests)

data-testid contracts (the implementation MUST provide these)
-------------------------------------------------------------
Welcome / Setup:
  welcome-heading, api-key-input, test-key-btn, save-key-btn,
  api-key-provider-link, api-key-cost-info, api-key-status

Playthrough creation:
  create-playthrough-heading, playthrough-name-input,
  game-title-input, create-playthrough-btn

Chat view:
  chat-container, playthrough-title, message-input, send-btn,
  user-message, ai-message, typing-indicator
"""

import re

from playwright.sync_api import Page, expect


# ── Helpers ───────────────────────────────────────────────────────────────


def _enter_api_key(page: Page, app_url: str, key: str = "test-key-valid"):
    """Navigate to the app and submit an API key on the welcome screen."""
    page.goto(app_url)
    page.get_by_test_id("api-key-input").fill(key)
    page.get_by_test_id("save-key-btn").click()
    # Should transition to playthrough-creation screen
    expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
        timeout=5_000
    )


def _create_playthrough(page: Page, name: str, game_title: str = ""):
    """Fill the playthrough creation form and submit."""
    page.get_by_test_id("playthrough-name-input").fill(name)
    if game_title:
        page.get_by_test_id("game-title-input").fill(game_title)
    page.get_by_test_id("create-playthrough-btn").click()
    # Chat view should now be visible
    expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)


def _send_message(page: Page, text: str):
    """Type a chat message and press Send."""
    page.get_by_test_id("message-input").fill(text)
    page.get_by_test_id("send-btn").click()


def _full_setup(
    page: Page,
    app_url: str,
    playthrough: str = "BG3 – Dark Urge Run",
    game_title: str = "",
):
    """Complete first-time setup: API key → playthrough → chat ready."""
    _enter_api_key(page, app_url)
    _create_playthrough(page, playthrough, game_title)


# ── 1. Welcome / Setup Screen ────────────────────────────────────────────


class TestWelcomeScreen:
    """Verify the first-time setup screen (User Flow 6.1, steps 1–2)."""

    def test_new_user_sees_welcome(self, page: Page, app_url: str):
        """A brand-new user (no stored API key) sees the welcome screen."""
        page.goto(app_url)
        expect(page.get_by_test_id("welcome-heading")).to_be_visible()
        expect(page.get_by_test_id("api-key-input")).to_be_visible()

    def test_provider_link_shown(self, page: Page, app_url: str):
        """A direct link to the Gemini API-key page is present (spec §6.1)."""
        page.goto(app_url)
        link = page.get_by_test_id("api-key-provider-link")
        expect(link).to_be_visible()
        expect(link).to_have_attribute("href", re.compile(r"https://"))

    def test_cost_info_shown(self, page: Page, app_url: str):
        """Brief free-tier / cost information is visible (spec §6.1)."""
        page.goto(app_url)
        expect(page.get_by_test_id("api-key-cost-info")).to_be_visible()


# ── 2. API Key Validation ────────────────────────────────────────────────


class TestApiKeyValidation:
    """Verify key entry, test button, and error states (User Flow 6.1, steps 2–3)."""

    def test_test_button_shows_success_for_valid_key(self, page: Page, app_url: str):
        """Pressing 'Test Key' with a valid key shows a success message."""
        page.goto(app_url)
        page.get_by_test_id("api-key-input").fill("test-key-valid")
        page.get_by_test_id("test-key-btn").click()

        status = page.get_by_test_id("api-key-status")
        expect(status).to_be_visible(timeout=5_000)
        expect(status).to_contain_text("valid", ignore_case=True)

    def test_test_button_shows_error_for_invalid_key(self, page: Page, app_url: str):
        """Pressing 'Test Key' with a bad key shows an error."""
        page.goto(app_url)
        page.get_by_test_id("api-key-input").fill("bad-key")
        page.get_by_test_id("test-key-btn").click()

        status = page.get_by_test_id("api-key-status")
        expect(status).to_be_visible(timeout=5_000)
        expect(status).to_contain_text("invalid", ignore_case=True)

    def test_save_navigates_to_playthrough_creation(self, page: Page, app_url: str):
        """Saving a valid key transitions to the 'create playthrough' screen."""
        page.goto(app_url)
        page.get_by_test_id("api-key-input").fill("test-key-valid")
        page.get_by_test_id("save-key-btn").click()
        expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
            timeout=5_000
        )


# ── 3. Playthrough Creation ──────────────────────────────────────────────


class TestPlaythroughCreation:
    """Verify playthrough creation flow (User Flow 6.1, steps 4–6; F1.1)."""

    def test_create_with_name_opens_chat(self, page: Page, app_url: str):
        """Creating a playthrough with just a name opens the chat view."""
        _enter_api_key(page, app_url)
        page.get_by_test_id("playthrough-name-input").fill("BG3 – Dark Urge Run")
        page.get_by_test_id("create-playthrough-btn").click()

        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "BG3 – Dark Urge Run"
        )

    def test_create_with_optional_game_title(self, page: Page, app_url: str):
        """The optional game-title field is accepted (spec F1.1)."""
        _enter_api_key(page, app_url)
        page.get_by_test_id("playthrough-name-input").fill("My Elden Ring Run")
        page.get_by_test_id("game-title-input").fill("Elden Ring")
        page.get_by_test_id("create-playthrough-btn").click()

        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)


# ── 4. Chat – Send & Receive ─────────────────────────────────────────────


class TestChatSendReceive:
    """Verify core chat interaction (F2.1, F2.6, M1 acceptance criteria)."""

    def test_send_message_and_get_ai_response(self, page: Page, app_url: str):
        """Full flow: setup → send message → receive non-empty AI response."""
        _full_setup(page, app_url)
        _send_message(page, "What class should I pick for a sneaky character?")

        ai_msg = page.get_by_test_id("ai-message").last
        expect(ai_msg).to_be_visible(timeout=30_000)
        # Mock LLM returns a deterministic response; just verify non-empty
        expect(ai_msg).not_to_be_empty()

    def test_user_message_displayed(self, page: Page, app_url: str):
        """The user's own message appears in the chat timeline."""
        _full_setup(page, app_url)
        _send_message(page, "Hello, LoreKeeper!")

        user_msg = page.get_by_test_id("user-message").last
        expect(user_msg).to_contain_text("Hello, LoreKeeper!")

    def test_typing_indicator_visible_while_waiting(self, page: Page, app_url: str):
        """A typing/thinking indicator is shown while the AI responds (F2.6)."""
        _full_setup(page, app_url)
        _send_message(page, "Tell me about stealth builds")

        # Indicator should appear shortly after send
        expect(page.get_by_test_id("typing-indicator")).to_be_visible(timeout=3_000)

        # After response arrives, indicator should vanish
        expect(page.get_by_test_id("ai-message").last).to_be_visible(timeout=30_000)
        expect(page.get_by_test_id("typing-indicator")).to_be_hidden()


# ── 5. Chat Persistence ──────────────────────────────────────────────────


class TestChatPersistence:
    """Chat history persists across browser refreshes (F2.5, M1 criteria)."""

    def test_messages_survive_page_reload(self, page: Page, app_url: str):
        """After a full page reload, previous messages are still visible."""
        _full_setup(page, app_url)
        _send_message(page, "Remember this across refresh")

        # Wait for AI response (ensures server has persisted the exchange)
        expect(page.get_by_test_id("ai-message").last).to_be_visible(timeout=30_000)

        # Reload the page
        page.reload()

        # Should auto-navigate to last active playthrough (spec F1.4)
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("user-message").last).to_contain_text(
            "Remember this across refresh"
        )
        expect(page.get_by_test_id("ai-message").last).to_be_visible()


# ── 6. Dark Mode ─────────────────────────────────────────────────────────


class TestDarkMode:
    """App uses dark mode by default (spec F2.3)."""

    def test_dark_theme_on_first_load(self, page: Page, app_url: str):
        """The <html> element carries a dark-theme indicator on first load."""
        page.goto(app_url)

        html = page.locator("html")
        # PicoCSS uses data-theme="dark"; other frameworks may use class="dark"
        theme = html.get_attribute("data-theme") or ""
        cls = html.get_attribute("class") or ""
        assert "dark" in theme.lower() or "dark" in cls.lower(), (
            f"Expected dark theme on <html>, "
            f"got data-theme='{theme}' class='{cls}'"
        )
