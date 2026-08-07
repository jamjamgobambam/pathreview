"""Tests for the API reference documentation (docs/API.md).

Guards issue #89: the API reference must document the POST /profiles request
body so the doc alone is enough to call the endpoint. These tests fail if that
schema is removed or drifts from the actual endpoint contract.
"""

from pathlib import Path

import pytest

API_DOC = Path(__file__).resolve().parents[2] / "docs" / "API.md"


@pytest.mark.unit
class TestApiDocsProfilesRequestBody:
    """Test suite ensuring docs/API.md documents the POST /profiles request body."""

    def _doc_text(self) -> str:
        """Read the API reference doc as text."""
        return API_DOC.read_text(encoding="utf-8")

    def test_api_doc_exists(self) -> None:
        """docs/API.md exists and is not empty."""
        assert API_DOC.is_file()
        assert self._doc_text().strip()

    def test_documents_multipart_content_type(self) -> None:
        """The request body is documented as multipart/form-data."""
        assert "multipart/form-data" in self._doc_text()

    def test_documents_all_request_fields(self) -> None:
        """All three request body fields are documented."""
        doc = self._doc_text()
        for field in ("github_username", "portfolio_url", "resume_file"):
            assert field in doc

    def test_documents_auth_requirement(self) -> None:
        """The Bearer-token requirement and 401 response are documented."""
        doc = self._doc_text()
        assert "Bearer" in doc
        assert "401" in doc

    def test_documents_allowed_resume_types(self) -> None:
        """All accepted resume MIME types, including plain text, are documented."""
        doc = self._doc_text()
        for mime in ("application/pdf", "text/markdown", "text/plain"):
            assert mime in doc

    def test_documents_invalid_file_type_response(self) -> None:
        """The 422 response and its exact detail message are documented."""
        doc = self._doc_text()
        assert "422" in doc
        assert "Resume must be a PDF or Markdown file" in doc

    def test_documents_curl_example(self) -> None:
        """A runnable curl example for POST /profiles is documented."""
        doc = self._doc_text()
        assert "curl" in doc
        assert "/profiles" in doc
