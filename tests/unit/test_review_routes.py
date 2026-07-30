"""Tests for POST /reviews via HTTP — create_review_endpoint validation."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Tests for the pre-creation validation added to create_review_endpoint."""

    def _make_client(self, mock_db_session, mock_user):
        async def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        return TestClient(app, raise_server_exceptions=False)

    def teardown_method(self, method):
        app.dependency_overrides.clear()

    def _mock_profile_query(self, mock_db_session, profile):
        """Wire db.execute() → scalars().first() → profile."""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = profile
        mock_db_session.execute = AsyncMock(return_value=mock_result)

    def test_empty_profile_returns_422(self):
        """POST /reviews returns 422 when the profile has no ingested documents."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        empty_profile = Mock()
        empty_profile.id = uuid4()
        empty_profile.user_id = mock_user.id
        empty_profile.github_username = None
        empty_profile.resume_text = None
        empty_profile.portfolio_url = None

        self._mock_profile_query(mock_db, empty_profile)

        client = self._make_client(mock_db, mock_user)
        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 422

    def test_profile_not_found_returns_404(self):
        """POST /reviews returns 404 when the profile_id does not exist."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        self._mock_profile_query(mock_db, None)

        client = self._make_client(mock_db, mock_user)
        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 404

    def test_empty_string_fields_returns_422(self):
        """POST /reviews returns 422 when all document fields are empty strings."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        profile = Mock()
        profile.id = uuid4()
        profile.user_id = mock_user.id
        profile.github_username = ""
        profile.resume_text = ""
        profile.portfolio_url = ""

        self._mock_profile_query(mock_db, profile)

        client = self._make_client(mock_db, mock_user)
        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 422

    def test_profile_with_only_github_username_succeeds(self):
        """POST /reviews returns 200 when at least one document field is set."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        profile = Mock()
        profile.id = uuid4()
        profile.user_id = mock_user.id
        profile.github_username = "octocat"
        profile.resume_text = None
        profile.portfolio_url = None

        self._mock_profile_query(mock_db, profile)

        from datetime import datetime
        mock_review = Mock()
        mock_review.id = uuid4()
        mock_review.profile_id = profile.id
        mock_review.status = "pending"
        mock_review.sections = None
        mock_review.overall_score = None
        mock_review.error_message = None
        mock_review.created_at = datetime.utcnow()
        mock_review.updated_at = datetime.utcnow()

        with patch("api.routes.reviews.create_review", new=AsyncMock(return_value=mock_review)):
            client = self._make_client(mock_db, mock_user)
            response = client.post("/reviews", json={"profile_id": str(profile.id)})

        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_422_error_message_mentions_documents(self):
        """422 detail message should guide the user to add a document."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        empty_profile = Mock()
        empty_profile.id = uuid4()
        empty_profile.user_id = mock_user.id
        empty_profile.github_username = None
        empty_profile.resume_text = None
        empty_profile.portfolio_url = None

        self._mock_profile_query(mock_db, empty_profile)

        client = self._make_client(mock_db, mock_user)
        response = client.post("/reviews", json={"profile_id": str(uuid4())})

        detail = response.json()["detail"].lower()
        assert "document" in detail or "github" in detail or "resume" in detail

    def test_empty_profile_does_not_call_create_review(self):
        """No review record should be created when the profile has no documents."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_db = AsyncMock()

        empty_profile = Mock()
        empty_profile.id = uuid4()
        empty_profile.user_id = mock_user.id
        empty_profile.github_username = None
        empty_profile.resume_text = None
        empty_profile.portfolio_url = None

        self._mock_profile_query(mock_db, empty_profile)

        with patch("api.routes.reviews.create_review", new=AsyncMock()) as mock_create:
            client = self._make_client(mock_db, mock_user)
            client.post("/reviews", json={"profile_id": str(uuid4())})
            mock_create.assert_not_called()
