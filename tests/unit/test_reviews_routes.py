"""Tests for the POST /reviews route, including profiles with no ingested documents."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db
from core.models.review import Review
from core.models.user import User


def _make_pending_review(profile_id) -> Review:
    now = datetime.utcnow()
    return Review(
        id=str(uuid4()),
        profile_id=str(profile_id),
        status="pending",
        sections=None,
        overall_score=None,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.unit
class TestCreateReviewEndpointNoIngestedDocuments:
    """POST /reviews for a profile that has no ingested documents (no resume/github/portfolio)."""

    @pytest.fixture(autouse=True)
    def override_dependencies(self):
        fake_user = User(id=str(uuid4()), email="student@example.com", hashed_password="hashed")

        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()
        try:
            yield fake_user
        finally:
            app.dependency_overrides.clear()

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_create_review_returns_pending_for_profile_with_no_documents(self, client):
        """Creating a review for a documentless profile still succeeds with status='pending'."""
        profile_id = uuid4()
        review = _make_pending_review(profile_id)

        with (
            patch(
                "api.routes.reviews.create_review", new=AsyncMock(return_value=review)
            ) as mock_create,
            patch("api.routes.reviews.process_review", new=AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(profile_id)})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending"
        assert body["sections"] is None
        assert body["overall_score"] is None

        mock_create.assert_awaited_once()
        assert mock_create.call_args.kwargs["profile_id"] == profile_id

    def test_create_review_schedules_processing_for_profile_with_no_documents(self, client):
        """Review creation still enqueues background processing even with zero ingested sources."""
        profile_id = uuid4()
        review = _make_pending_review(profile_id)

        with (
            patch("api.routes.reviews.create_review", new=AsyncMock(return_value=review)),
            patch("api.routes.reviews.process_review", new=AsyncMock()) as mock_process,
        ):
            client.post("/reviews", json={"profile_id": str(profile_id)})

        mock_process.assert_awaited_once()
        _, called_review_id, called_profile_id = mock_process.call_args.args
        assert called_review_id == review.id
        assert called_profile_id == profile_id

    def test_create_review_error_response_still_returns_500_on_service_failure(self, client):
        """Sanity check: unrelated service failures still surface as a 500,
        not a silent pending review."""
        profile_id = uuid4()

        with patch(
            "api.routes.reviews.create_review",
            new=AsyncMock(side_effect=RuntimeError("db unavailable")),
        ):
            response = client.post("/reviews", json={"profile_id": str(profile_id)})

        assert response.status_code == 500
