"""Tests for the POST /reviews endpoint in api/routes/reviews.py"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test suite for POST /reviews."""

    @pytest.fixture
    def mock_user(self) -> Mock:
        """Create a mock authenticated user."""
        user = Mock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def client(self, mock_user):
        """Create a TestClient with auth and database dependencies overridden."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    def empty_profile(self) -> Mock:
        """Create a mock Profile with no ingested documents."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        profile.resume_filename = None
        return profile

    @pytest.fixture
    def pending_review(self) -> Mock:
        """Create a mock Review as create_review would return it."""
        review = Mock()
        review.id = uuid4()
        review.profile_id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        review.error_message = None
        review.created_at = "2026-01-01T00:00:00Z"
        review.updated_at = "2026-01-01T00:00:00Z"
        return review

    def test_empty_profile_returns_422(self, client, empty_profile):
        """Test profile with no ingested documents is rejected."""
        with patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)):
            response = client.post("/reviews", json={"profile_id": str(empty_profile.id)})

        assert response.status_code == 422
        assert "no ingested documents" in response.json()["detail"].lower()

    def test_empty_profile_creates_no_review(self, client, empty_profile):
        """Test rejection happens before a pending review row is created."""
        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)),
            patch("api.routes.reviews.create_review", AsyncMock()) as mock_create,
        ):
            client.post("/reviews", json={"profile_id": str(empty_profile.id)})

        mock_create.assert_not_called()

    def test_whitespace_only_fields_return_422(self, client, empty_profile):
        """Test whitespace-only source fields count as no documents."""
        empty_profile.github_username = "   "
        empty_profile.portfolio_url = ""

        with patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)):
            response = client.post("/reviews", json={"profile_id": str(empty_profile.id)})

        assert response.status_code == 422

    def test_github_username_only_is_accepted(self, client, empty_profile, pending_review):
        """Test a profile with only a GitHub username is accepted."""
        empty_profile.github_username = "octocat"

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)),
            patch(
                "api.routes.reviews.create_review",
                AsyncMock(return_value=pending_review),
            ),
            patch("api.routes.reviews.process_review", AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(empty_profile.id)})

        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_portfolio_url_only_is_accepted(self, client, empty_profile, pending_review):
        """Test a profile with only a portfolio URL is accepted."""
        empty_profile.portfolio_url = "https://example.com"

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)),
            patch(
                "api.routes.reviews.create_review",
                AsyncMock(return_value=pending_review),
            ),
            patch("api.routes.reviews.process_review", AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(empty_profile.id)})

        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_resume_text_only_is_accepted(self, client, empty_profile, pending_review):
        """Test a profile with only resume text is accepted."""
        empty_profile.resume_text = "Jane Doe, Software Engineer"

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)),
            patch(
                "api.routes.reviews.create_review",
                AsyncMock(return_value=pending_review),
            ),
            patch("api.routes.reviews.process_review", AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(empty_profile.id)})

        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_missing_profile_returns_404(self, client):
        """Test a profile that does not exist or is not owned returns 404."""
        with patch("api.routes.reviews.get_profile", AsyncMock(return_value=None)):
            response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 404
        assert response.json()["detail"] == "Profile not found"

    def test_profile_lookup_is_scoped_to_current_user(self, client, mock_user):
        """Test the profile lookup is scoped to the authenticated user."""
        profile_id = uuid4()

        with patch(
            "api.routes.reviews.get_profile", AsyncMock(return_value=None)
        ) as mock_get_profile:
            client.post("/reviews", json={"profile_id": str(profile_id)})

        assert mock_get_profile.await_args.kwargs["user_id"] == mock_user.id
        assert mock_get_profile.await_args.kwargs["profile_id"] == profile_id
