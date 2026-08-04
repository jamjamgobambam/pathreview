"""Route-level tests for POST /reviews (api/routes/reviews.py).

These are the first tests in the repo that exercise the HTTP layer (routing,
auth dependency, validation, response serialization) rather than calling
service functions directly.

NOTE: TestClient(app) is deliberately used WITHOUT the `with` context manager.
Entering the context manager fires the app's startup event, which calls
init_db() and attempts a real database connection. The plain client skips
lifespan events entirely, so these tests run against mocked dependencies only.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db


def make_profile(
    github_username: str | None = None,
    portfolio_url: str | None = None,
    resume_text: str | None = None,
) -> Mock:
    """Create a mock Profile with the given content fields."""
    profile = Mock()
    profile.id = uuid4()
    profile.github_username = github_username
    profile.portfolio_url = portfolio_url
    profile.resume_text = resume_text
    return profile


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Tests for POST /reviews profile-content validation (issue #88)."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        return session

    @pytest.fixture
    def client(self, mock_db_session: AsyncMock) -> Iterator[TestClient]:
        """TestClient with auth and DB dependencies overridden."""
        user = Mock()
        user.id = uuid4()
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: mock_db_session
        yield TestClient(app)
        app.dependency_overrides.clear()

    @staticmethod
    def profile_lookup_returns(session: AsyncMock, profile: Mock | None) -> None:
        """Make the session's profile query return the given profile.

        The result is a plain Mock (not AsyncMock): `await db.execute(...)`
        returns it, then `.scalars().first()` is called synchronously.
        """
        result = Mock()
        result.scalars.return_value.first.return_value = profile
        session.execute = AsyncMock(return_value=result)

    def test_profile_not_found_returns_404(
        self, client: TestClient, mock_db_session: AsyncMock
    ) -> None:
        """POST /reviews returns 404 when the profile doesn't exist or isn't owned."""
        self.profile_lookup_returns(mock_db_session, None)

        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 404
        assert response.json()["detail"] == "Profile not found"
        mock_db_session.add.assert_not_called()

    def test_no_ingested_content_returns_422(
        self, client: TestClient, mock_db_session: AsyncMock
    ) -> None:
        """POST /reviews returns 422 and creates no Review row for an empty profile."""
        self.profile_lookup_returns(mock_db_session, make_profile())

        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 422
        assert response.json()["detail"] == "Profile has no ingested content to review"
        mock_db_session.add.assert_not_called()

    def test_whitespace_only_content_returns_422(
        self, client: TestClient, mock_db_session: AsyncMock
    ) -> None:
        """Whitespace-only fields don't count as reviewable content."""
        self.profile_lookup_returns(mock_db_session, make_profile(github_username="   "))

        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 422
        mock_db_session.add.assert_not_called()

    def test_profile_with_content_creates_pending_review(
        self, client: TestClient, mock_db_session: AsyncMock
    ) -> None:
        """Regression: the new validation must not block profiles with real content."""
        profile = make_profile(github_username="octocat")
        self.profile_lookup_returns(mock_db_session, profile)

        async def stamp_db_defaults(instance: Any) -> None:
            # Mimic what db.refresh does after INSERT: populate column defaults.
            instance.id = str(uuid4())
            instance.created_at = datetime.utcnow()
            instance.updated_at = datetime.utcnow()

        mock_db_session.refresh = AsyncMock(side_effect=stamp_db_defaults)

        # The background task would run synchronously after the response and
        # exercise the real pipeline against the mock session -- not under test.
        with patch("api.routes.reviews.process_review", new=AsyncMock()):
            response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending"
        assert body["sections"] is None
        assert body["overall_score"] is None
        mock_db_session.add.assert_called_once()
