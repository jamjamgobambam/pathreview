"""Tests for API request schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.schemas.profile import ProfileCreate
from api.schemas.review import ReviewCreate


@pytest.mark.unit
class TestApiSchemas:
    """Test suite for validating API request schemas."""

    def test_profile_create_valid(self) -> None:
        """Test ProfileCreate with valid fields."""
        schema = ProfileCreate(
            github_username="test-user",
            portfolio_url="https://example.com",
        )
        assert schema.github_username == "test-user"
        assert schema.portfolio_url == "https://example.com"

    def test_profile_create_empty(self) -> None:
        """Test ProfileCreate handles empty fields (both are optional)."""
        schema = ProfileCreate()
        assert schema.github_username is None
        assert schema.portfolio_url is None

    def test_profile_create_username_too_long(self) -> None:
        """Test ProfileCreate raises error when github_username exceeds 255 chars."""
        long_username = "a" * 256
        with pytest.raises(ValidationError):
            ProfileCreate(github_username=long_username)

    def test_profile_create_portfolio_url_too_long(self) -> None:
        """Test ProfileCreate raises error when portfolio_url exceeds 500 chars."""
        long_url = "https://example.com/" + "a" * 500
        with pytest.raises(ValidationError):
            ProfileCreate(portfolio_url=long_url)

    def test_review_create_valid(self) -> None:
        """Test ReviewCreate with a valid UUID."""
        profile_uuid = uuid4()
        schema = ReviewCreate(profile_id=profile_uuid)
        assert schema.profile_id == profile_uuid

    def test_review_create_invalid_uuid(self) -> None:
        """Test ReviewCreate raises validation error for invalid UUID types."""
        with pytest.raises(ValidationError):
            # Pass a string that is not a valid UUID format
            ReviewCreate(profile_id="not-a-uuid")

    def test_review_create_missing_profile_id(self) -> None:
        """Test ReviewCreate raises validation error when profile_id is missing."""
        with pytest.raises(ValidationError):
            ReviewCreate()
