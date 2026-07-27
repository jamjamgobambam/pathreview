"""Tests for reviews routes - issue #88 reproduction."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db
from core.models.profile import Profile
from core.models.user import User


@pytest.mark.unit
class TestCreateReviewNoIngestedContent:
    """Reproduction test suite for issue #88."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated User."""
        user = Mock(spec=User)
        user.id = str(uuid4())
        return user

    @pytest.fixture
    def mock_profile_no_content(self):
        """A profile that exists but has no github/portfolio/resume data."""
        profile = Mock(spec=Profile)
        profile.id = str(uuid4())
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        return profile

    @pytest.fixture
    def client(self, mock_user):
        """TestClient with get_db/get_current_user overridden and DB startup mocked."""

        async def _override_get_db():
            session = AsyncMock()
            session.add = Mock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()
            yield session

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _override_get_db

        with patch("api.main.init_db", new=AsyncMock()):
            with TestClient(app) as test_client:
                yield test_client

        app.dependency_overrides.clear()

    def test_create_review_for_profile_with_no_ingested_content_returns_error(
        self, client, mock_profile_no_content
    ):
        """POST /reviews for a profile with no ingested content should return an error, not 200.

        Reproduction of issue #88: create_review_endpoint currently has no
        check for missing ingested content, so this assertion fails today
        (actual response is 200) instead of the expected 422.
        """
        now = datetime.now(UTC)
        mock_review = Mock()
        mock_review.id = uuid4()
        mock_review.profile_id = UUID(mock_profile_no_content.id)
        mock_review.status = "pending"
        mock_review.sections = None
        mock_review.overall_score = None
        mock_review.error_message = None
        mock_review.created_at = now
        mock_review.updated_at = now

        with (
            patch("core.services.review_service.Review", return_value=mock_review),
            patch("api.routes.reviews.process_review", new=AsyncMock()),
        ):
            response = client.post(
                "/reviews",
                json={"profile_id": mock_profile_no_content.id},
            )

        assert response.status_code == 422, (
            "Expected the endpoint to reject a profile with no ingested "
            f"content, but got {response.status_code}: {response.text}"
        )
