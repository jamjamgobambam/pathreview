"""Tests for the review routes in api/routes/reviews.py.

Focus (issue 88): POST /reviews when the target profile has no content to
review. This is the repo's first HTTP-endpoint test, so it establishes the
pattern of using FastAPI's TestClient with `app.dependency_overrides` to fake
authentication and the database, plus patching the service-layer functions the
route calls (get_profile / create_review / process_review) so the test exercises
only the endpoint's own logic.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db


@pytest.mark.unit
class TestCreateReviewRoute:
    """POST /reviews — validation of the target profile before processing."""

    @pytest.fixture(autouse=True)
    def override_auth_and_db(self):
        # Replace the real auth + DB dependencies so the endpoint runs entirely
        # in memory: no JWT to decode, no database connection to open. Every test
        # in this class gets these overrides automatically (autouse).
        fake_user = SimpleNamespace(id=uuid4())
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()
        self.fake_user = fake_user
        yield
        # Clear overrides so state never leaks into other tests.
        app.dependency_overrides.clear()

    @staticmethod
    def _profile(*, github=None, resume=None, portfolio=None):
        # Stand-in for a Profile row. Attributes are set explicitly (not left as
        # auto-created Mock attributes) so the route's "has no content" check
        # sees real None values instead of truthy mocks.
        return SimpleNamespace(
            id=uuid4(),
            github_username=github,
            resume_text=resume,
            portfolio_url=portfolio,
        )

    def test_profile_with_no_content_returns_422(self):
        """A profile with no github/resume/portfolio is rejected with 422.

        This is the case the issue describes: the endpoint must return an
        appropriate client error, not crash and not silently succeed.
        """
        empty_profile = self._profile()  # all three source fields are None
        with patch(
            "api.routes.reviews.get_profile",
            AsyncMock(return_value=empty_profile),
        ):
            client = TestClient(app)
            response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 422
        assert response.json()["detail"] == "Profile has no content to review"

    def test_missing_or_unowned_profile_returns_404(self):
        """When get_profile returns None (missing or not owned), respond 404.

        Loading the profile forces us to handle the None case; without it, the
        content check would dereference None and surface as a 500.
        """
        with patch(
            "api.routes.reviews.get_profile",
            AsyncMock(return_value=None),
        ):
            client = TestClient(app)
            response = client.post("/reviews", json={"profile_id": str(uuid4())})

        assert response.status_code == 404
        assert response.json()["detail"] == "Profile not found"

    def test_profile_with_content_is_accepted(self):
        """A profile with at least one source still returns 200 + "pending".

        Guards against the new validation over-rejecting valid profiles.
        """
        profile = self._profile(github="octocat")
        fake_review = SimpleNamespace(
            id=uuid4(),
            profile_id=profile.id,
            status="pending",
            sections=None,
            overall_score=None,
            error_message=None,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
        )
        # Patch the two service calls the happy path makes so no real DB work or
        # background processing happens; we only care that the endpoint accepts
        # the request and echoes back the pending review.
        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=profile)),
            patch("api.routes.reviews.create_review", AsyncMock(return_value=fake_review)),
            patch("api.routes.reviews.process_review", AsyncMock()),
        ):
            client = TestClient(app)
            response = client.post("/reviews", json={"profile_id": str(profile.id)})

        assert response.status_code == 200
        assert response.json()["status"] == "pending"
