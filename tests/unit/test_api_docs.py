"""Tests verifying that docs/API.md documents the request body schemas for POST endpoints."""

from pathlib import Path

import pytest

DOCS_PATH = Path(__file__).parents[2] / "docs" / "API.md"


@pytest.mark.unit
class TestApiDocumentation:
    """Verify that docs/API.md contains request body schemas for POST endpoints."""

    @pytest.fixture(autouse=True)
    def api_docs_content(self) -> None:
        self.content = DOCS_PATH.read_text()

    def test_post_profiles_documents_content_type(self) -> None:
        """POST /profiles request body content type should be documented."""
        assert "multipart/form-data" in self.content

    def test_post_profiles_documents_github_username_field(self) -> None:
        """POST /profiles request body should document the github_username field."""
        assert "github_username" in self.content

    def test_post_profiles_documents_portfolio_url_field(self) -> None:
        """POST /profiles request body should document the portfolio_url field."""
        assert "portfolio_url" in self.content

    def test_post_profiles_documents_resume_file_field(self) -> None:
        """POST /profiles request body should document the resume_file field."""
        assert "resume_file" in self.content

    def test_post_reviews_documents_content_type(self) -> None:
        """POST /reviews request body content type should be documented."""
        assert "application/json" in self.content

    def test_post_reviews_documents_profile_id_field(self) -> None:
        """POST /reviews request body should document the profile_id field."""
        assert "profile_id" in self.content
