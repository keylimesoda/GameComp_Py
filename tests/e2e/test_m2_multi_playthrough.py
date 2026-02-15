"""
M2: Multi-Playthrough — End-to-End Tests
=========================================

Tests for Milestone 2: user can manage multiple playthroughs and switch between
them.

Spec references
---------------
- Milestone M2 acceptance criteria              (spec.md §12)
- User Flow 6.3: Switching Playthroughs         (spec.md §6.3)
- F1.2  Rename playthrough and update game title
- F1.3  List playthroughs sorted by last played
- F1.4  Open to most recently active playthrough
- F1.5  Playthroughs completely siloed
- F1.6  Delete with confirmation

data-testid contracts (the implementation MUST provide these)
-------------------------------------------------------------
Header / navigation:
  sidebar-toggle          – hamburger / menu button to open playthrough list

Playthrough sidebar/list:
  playthrough-sidebar     – the sidebar/modal container
  playthrough-item        – one entry in the list (repeated)
  playthrough-last-played – "last played" timestamp on each item
  new-playthrough-btn     – "+ New Playthrough" button in the sidebar

Rename:
  rename-btn              – button to start renaming
  rename-name-input       – name input in rename form
  rename-game-title-input – game title input in rename form
  rename-save-btn         – save rename button

Delete:
  delete-btn              – button to initiate deletion
  delete-confirm-btn      – confirm deletion
  delete-cancel-btn       – cancel deletion
"""

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
    """Send a chat message and wait for AI response."""
    page.get_by_test_id("message-input").fill(text)
    page.get_by_test_id("send-btn").click()
    expect(page.get_by_test_id("ai-message").last).to_be_visible(timeout=30_000)


def _open_sidebar(page: Page):
    """Open the playthrough sidebar/list."""
    page.get_by_test_id("sidebar-toggle").click()
    expect(page.get_by_test_id("playthrough-sidebar")).to_be_visible(timeout=3_000)


def _create_two_playthroughs(page: Page, app_url: str):
    """Helper: set up key, create PT-A, then PT-B via sidebar. Ends on PT-B chat."""
    _setup_with_key(page, app_url)
    _create_playthrough(page, "Playthrough Alpha", "Baldur's Gate 3")
    # Create second via sidebar
    _open_sidebar(page)
    page.get_by_test_id("new-playthrough-btn").click()
    expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
        timeout=5_000
    )
    _create_playthrough(page, "Playthrough Beta", "Elden Ring")


# ── 1. Sidebar / Playthrough List ────────────────────────────────────────


class TestPlaythroughList:
    """Verify the playthrough selector sidebar (F1.3, User Flow 6.3)."""

    def test_sidebar_toggle_visible_in_chat(self, page: Page, app_url: str):
        """A menu/hamburger button is visible on the chat screen."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Test Run")
        expect(page.get_by_test_id("sidebar-toggle")).to_be_visible()

    def test_sidebar_shows_playthroughs(self, page: Page, app_url: str):
        """Opening the sidebar shows the list of playthroughs."""
        _create_two_playthroughs(page, app_url)
        _open_sidebar(page)
        items = page.get_by_test_id("playthrough-item")
        expect(items).to_have_count(2)

    def test_playthroughs_sorted_by_last_played(self, page: Page, app_url: str):
        """Most recently active playthrough appears first (F1.3)."""
        _create_two_playthroughs(page, app_url)
        # Beta was created last, so it should be first
        _open_sidebar(page)
        first_item = page.get_by_test_id("playthrough-item").first
        expect(first_item).to_contain_text("Playthrough Beta")

    def test_new_playthrough_button_in_sidebar(self, page: Page, app_url: str):
        """A '+ New Playthrough' button is present in the sidebar (User Flow 6.3 step 4)."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "First Run")
        _open_sidebar(page)
        expect(page.get_by_test_id("new-playthrough-btn")).to_be_visible()

    def test_last_played_timestamp_shown(self, page: Page, app_url: str):
        """Each playthrough in the list shows a 'last played' indicator."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Timed Run")
        _open_sidebar(page)
        expect(
            page.get_by_test_id("playthrough-last-played").first
        ).to_be_visible()


# ── 2. Create Additional Playthroughs ────────────────────────────────────


class TestCreateMultiplePlaythroughs:
    """Verify creating playthroughs beyond the first one."""

    def test_create_second_playthrough_via_sidebar(self, page: Page, app_url: str):
        """User can create a second playthrough from the sidebar."""
        _create_two_playthroughs(page, app_url)
        # Should now be on Playthrough Beta's chat
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "Playthrough Beta"
        )

    def test_both_playthroughs_in_list(self, page: Page, app_url: str):
        """Both playthroughs appear in the sidebar list."""
        _create_two_playthroughs(page, app_url)
        _open_sidebar(page)
        items = page.get_by_test_id("playthrough-item")
        expect(items).to_have_count(2)


# ── 3. Switch Between Playthroughs ───────────────────────────────────────


class TestSwitchPlaythrough:
    """Verify switching playthroughs (User Flow 6.3, F1.5 silo)."""

    def test_click_switches_to_selected_playthrough(self, page: Page, app_url: str):
        """Clicking a different playthrough in the sidebar switches the chat."""
        _create_two_playthroughs(page, app_url)
        # Currently on Beta; switch to Alpha
        _open_sidebar(page)
        page.get_by_test_id("playthrough-item").filter(
            has_text="Playthrough Alpha"
        ).click()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "Playthrough Alpha"
        )

    def test_chat_context_stays_siloed(self, page: Page, app_url: str):
        """Messages from one playthrough do NOT appear in another (F1.5)."""
        _create_two_playthroughs(page, app_url)
        # Send a message in Beta
        _send_message(page, "This is Beta-only content")

        # Switch to Alpha
        _open_sidebar(page)
        page.get_by_test_id("playthrough-item").filter(
            has_text="Playthrough Alpha"
        ).click()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        # Alpha should have NO messages at all
        expect(page.get_by_test_id("user-message")).to_have_count(0)

    def test_switch_back_preserves_messages(self, page: Page, app_url: str):
        """Switching away and back preserves the chat messages."""
        _create_two_playthroughs(page, app_url)
        _send_message(page, "Remember me in Beta")

        # Switch to Alpha then back to Beta
        _open_sidebar(page)
        page.get_by_test_id("playthrough-item").filter(
            has_text="Playthrough Alpha"
        ).click()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        _open_sidebar(page)
        page.get_by_test_id("playthrough-item").filter(
            has_text="Playthrough Beta"
        ).click()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)

        expect(page.get_by_test_id("user-message").last).to_contain_text(
            "Remember me in Beta"
        )


# ── 4. Rename Playthrough ────────────────────────────────────────────────


class TestRenamePlaythrough:
    """Verify renaming a playthrough and its game title (F1.2)."""

    def test_rename_updates_title(self, page: Page, app_url: str):
        """Renaming a playthrough updates the header and sidebar."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Old Name", "Old Game")

        # Open rename UI
        page.get_by_test_id("rename-btn").click()
        page.get_by_test_id("rename-name-input").fill("New Name")
        page.get_by_test_id("rename-save-btn").click()

        # Title in chat header should reflect the new name
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "New Name", timeout=5_000
        )

    def test_rename_updates_game_title(self, page: Page, app_url: str):
        """Updating the game title is persisted (F1.2)."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "My Run", "Old Game")

        page.get_by_test_id("rename-btn").click()
        page.get_by_test_id("rename-game-title-input").fill("New Game Title")
        page.get_by_test_id("rename-save-btn").click()

        # Verify by reopening rename form — game title should show new value
        expect(page.get_by_test_id("playthrough-title")).to_be_visible(timeout=5_000)
        page.get_by_test_id("rename-btn").click()
        expect(page.get_by_test_id("rename-game-title-input")).to_have_value(
            "New Game Title"
        )

    def test_renamed_playthrough_shows_in_sidebar(self, page: Page, app_url: str):
        """After rename, the sidebar reflects the new name."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Original Name")

        page.get_by_test_id("rename-btn").click()
        page.get_by_test_id("rename-name-input").fill("Renamed")
        page.get_by_test_id("rename-save-btn").click()
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "Renamed", timeout=5_000
        )

        _open_sidebar(page)
        expect(
            page.get_by_test_id("playthrough-item").first
        ).to_contain_text("Renamed")


# ── 5. Delete Playthrough ────────────────────────────────────────────────


class TestDeletePlaythrough:
    """Verify deleting a playthrough with confirmation (F1.6)."""

    def test_delete_shows_confirmation(self, page: Page, app_url: str):
        """Clicking delete shows a confirmation prompt, not immediate deletion."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Doomed Run")

        page.get_by_test_id("delete-btn").click()
        expect(page.get_by_test_id("delete-confirm-btn")).to_be_visible(timeout=3_000)
        expect(page.get_by_test_id("delete-cancel-btn")).to_be_visible()

    def test_cancel_delete_keeps_playthrough(self, page: Page, app_url: str):
        """Cancelling deletion keeps the playthrough intact."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Safe Run")

        page.get_by_test_id("delete-btn").click()
        page.get_by_test_id("delete-cancel-btn").click()

        # Still on the same playthrough
        expect(page.get_by_test_id("playthrough-title")).to_contain_text("Safe Run")

    def test_confirm_delete_removes_playthrough(self, page: Page, app_url: str):
        """Confirming deletion removes the playthrough entirely."""
        _create_two_playthroughs(page, app_url)

        # Delete Beta (currently active)
        page.get_by_test_id("delete-btn").click()
        page.get_by_test_id("delete-confirm-btn").click()

        # Should land on the remaining playthrough (Alpha) or the list
        # The sidebar should only show one playthrough now
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)
        _open_sidebar(page)
        expect(page.get_by_test_id("playthrough-item")).to_have_count(1)
        expect(page.get_by_test_id("playthrough-item").first).to_contain_text(
            "Playthrough Alpha"
        )

    def test_delete_last_playthrough_shows_creation_screen(
        self, page: Page, app_url: str
    ):
        """Deleting the only playthrough redirects to the creation screen."""
        _setup_with_key(page, app_url)
        _create_playthrough(page, "Only Run")

        page.get_by_test_id("delete-btn").click()
        page.get_by_test_id("delete-confirm-btn").click()

        expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
            timeout=5_000
        )


# ── 6. Returns to Last Active ────────────────────────────────────────────


class TestReturnsToLastActive:
    """Verify the app opens to the last active playthrough (F1.4)."""

    def test_reopen_lands_on_last_active(self, page: Page, app_url: str):
        """After creating two playthroughs, refreshing lands on the most recent."""
        _create_two_playthroughs(page, app_url)
        # Beta was created/used last
        page.reload()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "Playthrough Beta"
        )

    def test_switching_updates_last_active(self, page: Page, app_url: str):
        """Switching to a playthrough makes it the 'last active' on next load."""
        _create_two_playthroughs(page, app_url)
        # Switch to Alpha
        _open_sidebar(page)
        page.get_by_test_id("playthrough-item").filter(
            has_text="Playthrough Alpha"
        ).click()
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "Playthrough Alpha", timeout=5_000
        )

        # Reload — should land on Alpha since we switched to it
        page.reload()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("playthrough-title")).to_contain_text(
            "Playthrough Alpha"
        )
