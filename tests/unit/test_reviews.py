"""Tests for api/routes/reviews.py"""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.auth import get_current_user
from api.routes.reviews import router
from core.database import get_db


@pytest.fixture
def mock_user() -> Mock:
    """Create a mock authenticated user."""
    user = Mock()
    user.id = uuid4()
    return user


@pytest.fixture
def client(mock_user: Mock) -> Generator[TestClient, None, None]:
    """TestClient with only the reviews router mounted, auth/db dependencies overridden."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test suite for POST /reviews (create_review_endpoint)."""

    def test_returns_404_when_profile_not_owned_by_user(self, client: TestClient) -> None:
        """Returns 404 'Profile not found' when create_review() returns None."""
        with patch("api.routes.reviews.create_review", new=AsyncMock(return_value=None)):
            response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 404
        assert response.json() == {"detail": "Profile not found"}

    def test_returns_review_when_profile_owned_by_user(self, client: TestClient) -> None:
        """Returns 200 with the created review when create_review() succeeds."""
        profile_id = uuid4()
        review_id = uuid4()
        now = datetime.now(UTC)

        mock_review = Mock()
        mock_review.id = review_id
        mock_review.profile_id = profile_id
        mock_review.status = "pending"
        mock_review.sections = None
        mock_review.overall_score = None
        mock_review.error_message = None
        mock_review.created_at = now
        mock_review.updated_at = now

        with (
            patch("api.routes.reviews.create_review", new=AsyncMock(return_value=mock_review)),
            patch("api.routes.reviews.process_review", new=AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(profile_id)})

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(review_id)
        assert body["profile_id"] == str(profile_id)
        assert body["status"] == "pending"
