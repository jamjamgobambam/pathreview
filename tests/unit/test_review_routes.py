"""Tests for reviews routes - issue #88."""

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


def _mock_profile_lookup(mock_db_session, profile):
    """Configure mock_db_session.execute so get_profile() returns the given profile (or None).

    db.execute() is the only async part of SQLAlchemy's async API; the returned
    Result object's .scalars()/.first() are synchronous, so the result itself
    must be a plain Mock, not an AsyncMock.
    """
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = profile
    mock_db_session.execute = AsyncMock(return_value=mock_result)


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test suite for POST /reviews, covering issue #88 (no ingested content)."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated User."""
        user = Mock(spec=User)
        user.id = str(uuid4())
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

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
    def mock_profile_with_content(self):
        """A profile with a github username set."""
        profile = Mock(spec=Profile)
        profile.id = str(uuid4())
        profile.github_username = "octocat"
        profile.portfolio_url = None
        profile.resume_text = None
        return profile

    @pytest.fixture
    def client(self, mock_user, mock_db_session):
        """TestClient with get_db/get_current_user overridden and DB startup mocked."""

        async def _override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _override_get_db

        with patch("api.main.init_db", new=AsyncMock()), TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()

    def test_create_review_for_profile_with_no_ingested_content_returns_422(
        self, client, mock_db_session, mock_profile_no_content
    ):
        """POST /reviews for a profile with no ingested content returns 422, not a crash."""
        _mock_profile_lookup(mock_db_session, mock_profile_no_content)

        response = client.post(
            "/reviews",
            json={"profile_id": mock_profile_no_content.id},
        )

        assert response.status_code == 422
        assert "ingested content" in response.json()["detail"].lower()

    def test_create_review_for_missing_profile_returns_404(self, client, mock_db_session):
        """POST /reviews for a profile_id that doesn't exist (or isn't owned) returns 404."""
        _mock_profile_lookup(mock_db_session, None)

        response = client.post(
            "/reviews",
            json={"profile_id": str(uuid4())},
        )

        assert response.status_code == 404

    def test_create_review_for_profile_with_content_returns_pending(
        self, client, mock_db_session, mock_profile_with_content
    ):
        """POST /reviews for a profile with content still returns 200 with status pending."""
        _mock_profile_lookup(mock_db_session, mock_profile_with_content)

        now = datetime.now(UTC)
        mock_review = Mock()
        mock_review.id = uuid4()
        mock_review.profile_id = UUID(mock_profile_with_content.id)
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
                json={"profile_id": mock_profile_with_content.id},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "pending"
