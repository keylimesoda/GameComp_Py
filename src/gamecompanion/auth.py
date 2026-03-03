"""GitHub OAuth Device Flow authentication for LoreKeeper.

Implements the GitHub Device Authorization Grant (RFC 8628) so users
can authenticate by visiting a URL and entering a code, instead of
manually generating and pasting a Personal Access Token.

Requires a registered GitHub OAuth App with Device Flow enabled.
Set LOREKEEPER_GITHUB_CLIENT_ID env var or pass client_id directly.
"""

import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

_DEVICE_CODE_URL = "https://github.com/login/device/code"
_TOKEN_URL = "https://github.com/login/oauth/access_token"
_DEVICE_VERIFY_URL = "https://github.com/login/device"

# Scope needed for GitHub Models API
_SCOPES = "models:read"


def _post_form(url: str, data: dict) -> dict:
    """POST form data, return parsed JSON."""
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def request_device_code(client_id: str) -> dict:
    """Start the device flow — returns device_code, user_code, verification_uri, etc.

    Returns dict with keys:
        device_code: str — internal code for polling
        user_code: str — code the user enters at verification_uri
        verification_uri: str — URL to visit (https://github.com/login/device)
        expires_in: int — seconds until codes expire
        interval: int — minimum polling interval in seconds
    """
    result = _post_form(_DEVICE_CODE_URL, {
        "client_id": client_id,
        "scope": _SCOPES,
    })
    if "error" in result:
        raise RuntimeError(f"Device code request failed: {result.get('error_description', result['error'])}")
    return result


def poll_for_token(client_id: str, device_code: str, interval: int = 5,
                   expires_in: int = 900, callback=None) -> str | None:
    """Poll GitHub until the user authorizes or the code expires.

    Args:
        client_id: OAuth app client ID
        device_code: From request_device_code()
        interval: Minimum seconds between polls
        expires_in: Seconds until timeout
        callback: Optional callable(status: str) for progress updates

    Returns:
        Access token string, or None if expired/denied.
    """
    deadline = time.time() + expires_in
    poll_interval = interval

    while time.time() < deadline:
        time.sleep(poll_interval)

        result = _post_form(_TOKEN_URL, {
            "client_id": client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })

        if "access_token" in result:
            return result["access_token"]

        error = result.get("error", "")

        if error == "authorization_pending":
            if callback:
                callback("waiting")
            continue
        elif error == "slow_down":
            poll_interval = result.get("interval", poll_interval + 5)
            if callback:
                callback("slow_down")
            continue
        elif error == "expired_token":
            if callback:
                callback("expired")
            return None
        elif error == "access_denied":
            if callback:
                callback("denied")
            return None
        else:
            raise RuntimeError(f"Token poll error: {result.get('error_description', error)}")

    return None


def save_token(token: str, data_dir: Path) -> None:
    """Save the OAuth token to the data directory."""
    token_path = data_dir / "github_token.json"
    token_path.write_text(json.dumps({"access_token": token}, indent=2))
    # Restrict permissions on Unix
    try:
        token_path.chmod(0o600)
    except (OSError, AttributeError):
        pass


def load_token(data_dir: Path) -> str | None:
    """Load a saved OAuth token, if it exists."""
    token_path = data_dir / "github_token.json"
    if not token_path.exists():
        return None
    try:
        data = json.loads(token_path.read_text())
        return data.get("access_token")
    except (json.JSONDecodeError, OSError):
        return None


def validate_token(token: str) -> bool:
    """Check if a token is still valid by hitting the GitHub user API."""
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "LoreKeeper",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False
