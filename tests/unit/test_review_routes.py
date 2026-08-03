"""Tests for reviews routes (api/routes/reviews.py)"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db


@pytest.mark.unit
class TestReviewRoutes:
    """Test suite for POST /reviews route-level behavior."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated User."""
        user = Mock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def client(self, mock_user, mock_db_session):
        """TestClient with auth/db dependencies overridden (no real DB/Docker)."""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        async def _get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = _get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_create_review_with_no_ingested_documents_does_not_reject(
        self, client, mock_db_session
    ):
        """Test POST /reviews does not reject a profile with no ingested documents."""

        profile_id = uuid4()

        with patch("core.services.review_service.Review") as MockReview:
            mock_instance = MockReview.return_value
            mock_instance.id = uuid4()
            mock_instance.profile_id = profile_id
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None
            mock_instance.error_message = None
            mock_instance.created_at = datetime.now(UTC)
            mock_instance.updated_at = datetime.now(UTC)

            response = client.post("/reviews", json={"profile_id": str(profile_id)})

            # No validation for zero-source profiles; endpoint fabricates instead of erroring.
            assert response.status_code == 200
            assert response.json()["status"] == "pending"
