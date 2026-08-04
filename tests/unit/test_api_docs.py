"""
tests/unit/test_api_docs.py

Regression tests for docs/API.md content.
These verify the file exists and contains all documented endpoints,
including the two routes added in this PR that were previously missing:
PUT /profiles/{profile_id} and GET /reviews/{review_id}/status.
"""

import pathlib

DOCS_ROOT = pathlib.Path(__file__).parent.parent.parent / "docs"
API_MD = DOCS_ROOT / "API.md"


def test_api_docs_file_exists() -> None:
    """docs/API.md must exist at the expected path."""
    assert API_MD.exists(), f"docs/API.md not found at {API_MD}"


def test_api_docs_contains_auth_endpoints() -> None:
    """docs/API.md must document both authentication endpoints."""
    content = API_MD.read_text()
    assert "POST /auth/register" in content
    assert "POST /auth/login" in content


def test_api_docs_contains_all_profile_endpoints() -> None:
    """docs/API.md must document all four profile endpoints including PUT."""
    content = API_MD.read_text()
    assert "POST /profiles" in content
    assert "GET /profiles/{profile_id}" in content
    assert "PUT /profiles/{profile_id}" in content
    assert "DELETE /profiles/{profile_id}" in content


def test_api_docs_contains_all_review_endpoints() -> None:
    """docs/API.md must document all four review endpoints including status."""
    content = API_MD.read_text()
    assert "POST /reviews" in content
    assert "GET /reviews/{review_id}" in content
    assert "GET /reviews" in content
    assert "GET /reviews/{review_id}/status" in content


def test_api_docs_contains_curl_examples() -> None:
    """docs/API.md must contain curl examples for each endpoint."""
    content = API_MD.read_text()
    assert content.count("curl") >= 11


def test_api_docs_documents_login_form_data_requirement() -> None:
    """docs/API.md must warn that POST /auth/login uses form data not JSON."""
    content = API_MD.read_text()
    assert "form data" in content.lower() or "form-data" in content.lower()
