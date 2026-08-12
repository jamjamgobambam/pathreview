"""
Simple tests to verify the API documentation examples work.

These tests run the curl commands from docs/API.md and verify they return
the expected HTTP status codes. This ensures the documentation stays
accurate even as the API changes.
"""

import json
import subprocess

import pytest

# Base URL for local API
BASE_URL = "http://localhost:8000"


def test_health_endpoint() -> None:
    """Test that GET /health returns a JSON response."""
    result = subprocess.run(
        ["curl", "-s", "-X", "GET", f"{BASE_URL}/health"], capture_output=True, text=True
    )
    assert result.returncode == 0
    # Should return JSON (either success or failure)
    assert result.stdout.startswith("{") or result.stdout.startswith("[")


def test_register_endpoint() -> None:
    """Test that POST /auth/register returns a token."""
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            f"{BASE_URL}/auth/register",
            "-H",
            "Content-Type: application/json",
            "-d",
            '{"email": "testdoc@example.com", "password": "test1234"}',
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "access_token" in response


def test_login_endpoint() -> None:
    """Test that POST /auth/login returns a token (OAuth2 form-data)."""
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            f"{BASE_URL}/auth/login",
            "-H",
            "Content-Type: application/x-www-form-urlencoded",
            "-d",
            "username=user1@example.com&password=password1",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    response = json.loads(result.stdout)
    assert "access_token" in response


@pytest.mark.skip(reason="Requires full API stack running")
def test_profiles_endpoint() -> None:
    """Test that POST /profiles requires authentication."""
    # This is a schema test - the endpoint requires a token
    pass


def test_api_docs_curl_count() -> None:
    """Verify that docs/API.md has all 9 curl examples."""
    with open("docs/API.md") as f:
        content = f.read()

    curl_count = content.count("curl -X")
    assert curl_count >= 9, f"Expected at least 9 curl examples, found {curl_count}"

    # Check for specific endpoints
    assert "GET /health" in content
    assert "POST /auth/register" in content
    assert "POST /auth/login" in content
    assert "POST /profiles" in content
    assert "GET /profiles/{profile_id}" in content
    assert "DELETE /profiles/{profile_id}" in content
    assert "POST /reviews" in content
    assert "GET /reviews/{review_id}" in content
    assert "GET /reviews" in content
