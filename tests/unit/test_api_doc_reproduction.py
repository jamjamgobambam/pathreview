"""Reproduction test for issue #89.

https://github.com/ascherj/pathreview/issues/89

The API reference (``docs/API.md``) lists ``POST /profiles`` and ``POST /reviews``
as one-line endpoint summaries but never documents their request bodies. A reader
cannot tell which fields are accepted, which are required, or what content type to
send without reading the FastAPI routes and Pydantic schemas.

These tests assert that ``docs/API.md`` documents the request-body fields that are
actually accepted by the routes. They FAIL on the current documentation, which is
the reproduction of the gap. Week 9's fix should turn them green.

Sources of truth for the expected field names:
- ``api/routes/profiles.py`` / ``api/schemas/profile.py`` -> github_username,
  portfolio_url, resume_file (multipart/form-data).
- ``api/routes/reviews.py`` / ``api/schemas/review.py`` -> profile_id
  (application/json).
"""

from pathlib import Path

import pytest

API_DOC = Path(__file__).resolve().parents[2] / "docs" / "API.md"


@pytest.mark.unit
class TestApiDocRequestSchemas:
    """Reproduce issue #89: missing request-body documentation."""

    @pytest.fixture
    def api_doc_text(self) -> str:
        return API_DOC.read_text(encoding="utf-8")

    def test_post_profiles_documents_request_fields(self, api_doc_text: str) -> None:
        """POST /profiles accepts multipart form fields that must be documented."""
        expected_fields = ["github_username", "portfolio_url", "resume_file"]
        missing = [f for f in expected_fields if f not in api_doc_text]
        assert not missing, (
            "docs/API.md does not document the POST /profiles request body "
            f"fields: {missing}. See api/routes/profiles.py (issue #89)."
        )

    def test_post_profiles_documents_content_type(self, api_doc_text: str) -> None:
        """POST /profiles is a multipart upload; the content type must be stated."""
        assert "multipart/form-data" in api_doc_text, (
            "docs/API.md does not state that POST /profiles uses "
            "multipart/form-data. See api/routes/profiles.py (issue #89)."
        )

    def test_post_reviews_documents_json_request_body(self, api_doc_text: str) -> None:
        """POST /reviews takes an application/json body with a required profile_id.

        ``profile_id`` already appears in docs as a *path* parameter for the
        profile endpoints, so its bare presence proves nothing. The gap is that
        the JSON request body and its content type are never documented, so this
        asserts the content type is stated.
        """
        assert "application/json" in api_doc_text, (
            "docs/API.md does not document the POST /reviews JSON request body "
            "(no application/json content type stated). See api/routes/reviews.py "
            "and api/schemas/review.py (issue #89)."
        )
