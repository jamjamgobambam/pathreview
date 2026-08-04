"""Tests verifying docs/API.md stays in sync with the actual request schemas."""

from pathlib import Path

import pytest

from api.schemas.profile import ProfileCreate
from api.schemas.review import ReviewCreate

API_DOCS_PATH = Path(__file__).resolve().parents[2] / "docs" / "API.md"


@pytest.fixture
def api_docs_text() -> str:
    return API_DOCS_PATH.read_text(encoding="utf-8")


@pytest.mark.unit
class TestApiDocsSchemaConsistency:
    """Test suite ensuring documented request fields match the real Pydantic schemas."""

    def test_profiles_doc_lists_every_profile_create_field(self, api_docs_text: str) -> None:
        """Every field on ProfileCreate must appear in the POST /profiles docs section."""
        for field_name in ProfileCreate.model_fields:
            assert (
                field_name in api_docs_text
            ), f"ProfileCreate field '{field_name}' is missing from docs/API.md"

    def test_profiles_doc_documents_resume_upload(self, api_docs_text: str) -> None:
        """Resume upload field isn't part of ProfileCreate but must still be documented."""
        assert "resume_file" in api_docs_text

    def test_profiles_doc_notes_multipart_form(self, api_docs_text: str) -> None:
        """POST /profiles takes multipart form data, not JSON; the docs must say so."""
        assert "multipart/form-data" in api_docs_text

    def test_reviews_doc_lists_every_review_create_field(self, api_docs_text: str) -> None:
        """Every field on ReviewCreate must appear in the POST /reviews docs section."""
        for field_name in ReviewCreate.model_fields:
            assert (
                field_name in api_docs_text
            ), f"ReviewCreate field '{field_name}' is missing from docs/API.md"

    def test_reviews_doc_notes_json_body(self, api_docs_text: str) -> None:
        """POST /reviews takes a JSON body; the docs must say so."""
        assert "application/json" in api_docs_text
