"""Integration tests for API key save functionality.

Tests the API key setup flow:
- POST /setup/save-key saves API key and redirects to playthrough creation
- GET / shows playthrough creation page when API key is configured
- Configuration is properly persisted
"""

import pytest
import httpx
from starlette.testclient import TestClient

from .conftest import assert_status_ok, assert_contains_testid, assert_redirect_to


def test_api_key_save_redirects_to_playthrough_creation(app_client: TestClient):
    """POST /setup/save-key should save API key and redirect to new playthrough page."""
    response = app_client.post("/setup/save-key", data={
        "api_key": "test-key-valid",
        "tavily_api_key": ""
    })
    
    # Should redirect to playthrough creation
    assert_redirect_to(response, "/setup/new-playthrough")


def test_api_key_save_with_tavily_key(app_client: TestClient):
    """POST /setup/save-key should save both Gemini and Tavily API keys."""
    response = app_client.post("/setup/save-key", data={
        "api_key": "test-key-valid", 
        "tavily_api_key": "tavily-test-key"
    })
    
    # Should redirect to playthrough creation
    assert_redirect_to(response, "/setup/new-playthrough")


def test_root_shows_playthrough_creation_when_api_key_set(app_client: TestClient):
    """GET / should show playthrough creation page when API key is configured."""
    # First, save an API key
    app_client.post("/setup/save-key", data={
        "api_key": "test-key-valid"
    })
    
    # Now GET / should show playthrough creation instead of welcome
    response = app_client.get("/")
    assert_status_ok(response)
    
    content = response.text
    
    # Should have playthrough creation elements instead of welcome
    assert_contains_testid(content, "create-playthrough-heading")
    assert_contains_testid(content, "playthrough-name-input")
    assert_contains_testid(content, "game-title-input") 
    assert_contains_testid(content, "create-playthrough-btn")


def test_setup_new_playthrough_page_elements(app_client: TestClient):
    """GET /setup/new-playthrough should show playthrough creation form."""
    # First, save an API key so we can access the page
    app_client.post("/setup/save-key", data={
        "api_key": "test-key-valid"
    })
    
    response = app_client.get("/setup/new-playthrough")
    assert_status_ok(response)
    
    content = response.text
    
    # Should have playthrough creation elements
    assert_contains_testid(content, "create-playthrough-heading")
    assert_contains_testid(content, "playthrough-name-input")
    assert_contains_testid(content, "game-title-input")
    assert_contains_testid(content, "create-playthrough-btn")
    
    # Should mention creating a playthrough
    assert "playthrough" in content.lower()


def test_setup_new_playthrough_without_api_key_redirects(app_client: TestClient):
    """GET /setup/new-playthrough should redirect to welcome if no API key set.""" 
    # Try to access playthrough creation without setting API key
    response = app_client.get("/setup/new-playthrough")
    
    # Should redirect back to root (welcome page)
    assert_redirect_to(response, "/")


def test_api_key_save_missing_key_field(app_client: TestClient):
    """POST /setup/save-key should handle missing api_key field."""
    response = app_client.post("/setup/save-key", data={
        "tavily_api_key": "some-key"
    })
    
    # Should return error for missing required field
    assert response.status_code in (400, 422)