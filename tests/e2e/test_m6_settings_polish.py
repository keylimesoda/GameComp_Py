"""
M6: Settings & Polish — End-to-End Tests
========================================

Covers settings management, debug mode changelog, offline handling,
API error dialog, and export/import playthrough data.
"""

import json
from playwright.sync_api import Page, expect


def _setup_with_key(page: Page, app_url: str):
    page.goto(app_url)
    page.get_by_test_id("api-key-input").fill("test-key-valid")
    page.get_by_test_id("save-key-btn").click()
    expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(
        timeout=5_000
    )


def _create_playthrough(page: Page, name: str, game_title: str = ""):
    page.get_by_test_id("playthrough-name-input").fill(name)
    if game_title:
        page.get_by_test_id("game-title-input").fill(game_title)
    page.get_by_test_id("create-playthrough-btn").click()
    expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=5_000)


def _send_message(page: Page, text: str):
    user_count = page.get_by_test_id("user-message").count()
    page.get_by_test_id("message-input").fill(text)
    page.get_by_test_id("send-btn").click()
    expect(page.get_by_test_id("user-message")).to_have_count(
        user_count + 1, timeout=30_000
    )


class TestSettingsBasics:
    def test_settings_page_shows_fields_and_data_location(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M6 Settings", "Baldur's Gate 3")

        page.get_by_test_id("settings-btn").click()
        expect(page.get_by_test_id("settings-heading")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("gemini-key-input")).to_be_visible()
        expect(page.get_by_test_id("tavily-key-input")).to_be_visible()
        expect(page.get_by_test_id("debug-toggle")).to_be_visible()
        expect(page.get_by_test_id("data-location")).to_be_visible()

    def test_settings_save_persists_status(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M6 Settings Save", "BG3")

        page.get_by_test_id("settings-btn").click()
        page.get_by_test_id("gemini-key-input").fill("test-key-valid")
        page.get_by_test_id("tavily-key-input").fill("tavily-key-123")
        page.get_by_test_id("settings-save-btn").click()
        expect(page.get_by_test_id("settings-saved")).to_be_visible(timeout=5_000)
        expect(page.get_by_test_id("gemini-key-status")).to_contain_text("set")
        expect(page.get_by_test_id("tavily-key-status")).to_contain_text("set")


class TestDebugModeChangelog:
    def test_debug_mode_writes_changelog(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M6 Debug", "BG3")

        page.get_by_test_id("settings-btn").click()
        page.get_by_test_id("debug-toggle").check()
        page.get_by_test_id("settings-save-btn").click()
        expect(page.get_by_test_id("settings-saved")).to_be_visible(timeout=5_000)

        cfg_resp = page.request.get(app_url + "/test/get-config")
        assert cfg_resp.status == 200
        assert cfg_resp.json().get("debug_mode") is True

        page.goto(app_url + "/chat/1")
        _send_message(page, "My character Keth is a level 6 shadow monk with 18 DEX")
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("📌", timeout=10_000)

        resp = page.request.get(app_url + "/test/changelog")
        assert resp.status == 200
        data = resp.json()
        assert data.get("lines"), "Changelog should contain at least one entry"


class TestErrorHandling:
    def test_offline_error_message(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M6 Offline", "BG3")

        page.request.post(app_url + "/test/set-config", data=json.dumps({"force_offline": True}))
        _send_message(page, "Hello while offline")
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("offline", ignore_case=True)

    def test_api_rate_limit_dialog(self, page: Page, app_url: str):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M6 Rate Limit", "BG3")

        page.request.post(app_url + "/test/set-config", data=json.dumps({"force_api_error": "rate_limit"}))
        _send_message(page, "Trigger rate limit")
        last_ai = page.get_by_test_id("ai-message").last
        expect(last_ai).to_contain_text("Rate limit", ignore_case=True)
        expect(last_ai).to_contain_text("Details", ignore_case=True)


class TestExportImport:
    def test_export_import_playthrough(self, page: Page, app_url: str, tmp_path):
        _setup_with_key(page, app_url)
        _create_playthrough(page, "M6 Export", "BG3")
        _send_message(page, "Remember me for export")

        page.get_by_test_id("settings-btn").click()
        with page.expect_download() as download_info:
            page.get_by_test_id("export-playthrough-btn").click()
        download = download_info.value
        zip_path = tmp_path / "playthrough.zip"
        download.save_as(str(zip_path))

        page.request.post(app_url + "/test/reset")
        page.goto(app_url)
        page.get_by_test_id("api-key-input").fill("test-key-valid")
        page.get_by_test_id("save-key-btn").click()
        expect(page.get_by_test_id("create-playthrough-heading")).to_be_visible(timeout=5_000)

        page.goto(app_url + "/settings")
        page.set_input_files("input[type='file'][data-testid='import-file-input']", str(zip_path))
        page.get_by_test_id("import-playthrough-btn").click()
        expect(page.get_by_test_id("chat-container")).to_be_visible(timeout=10_000)
        # Verify message exists in imported playthrough
        expect(page.get_by_test_id("user-message").last).to_contain_text("Remember me for export")
