"""Route-level tests for POST/GET /reviews (issue #88).

Covers baseline coverage for the review routes and, per issue #88, documents
the current (unvalidated) behavior when a profile has no ingested documents:
`POST /reviews` still returns 200/"pending", and the background
`process_review` pipeline still completes with fabricated feedback sections
instead of surfacing the lack of ingested content.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db
from core.models.review import Review
from core.models.user import User
from core.services.review_service import process_review


def make_review_mock(**overrides):
    """Build a Mock standing in for a Review ORM instance with valid response fields.

    Uses spec=Review so accessing an attribute the model doesn't define (e.g. the
    route's `getattr(review, "progress_pct", 0)` probe) raises AttributeError and
    falls back to the default, instead of Mock auto-vivifying a child Mock that
    then fails JSON serialization.
    """
    review = Mock(spec=Review)
    review.id = overrides.get("id", uuid4())
    review.profile_id = overrides.get("profile_id", uuid4())
    review.status = overrides.get("status", "pending")
    review.sections = overrides.get("sections")
    review.overall_score = overrides.get("overall_score")
    review.error_message = overrides.get("error_message")
    review.created_at = overrides.get("created_at", datetime.utcnow())
    review.updated_at = overrides.get("updated_at", datetime.utcnow())
    return review


def make_execute_result(first_return_value=None, all_return_value=None):
    """Build a Mock standing in for the Result object returned by AsyncSession.execute().

    Must be a plain Mock (not AsyncMock) for the child .scalars() call — AsyncMock
    auto-specs child attributes as AsyncMock too, which turns .scalars().first()
    into an unawaited coroutine instead of the configured return value.
    """
    result = Mock()
    result.scalars.return_value.first.return_value = first_return_value
    result.scalars.return_value.all.return_value = all_return_value or []
    return result


@pytest.mark.unit
class TestReviewRoutes:
    """Route-level tests for POST /reviews and the GET /reviews read endpoints."""

    @pytest.fixture
    def fake_user(self):
        user = Mock(spec=User)
        user.id = str(uuid4())
        return user

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def client(self, fake_user, mock_db_session):
        async def override_get_current_user():
            return fake_user

        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        yield TestClient(app)

        app.dependency_overrides.clear()

    # ---- POST /reviews ----

    def test_create_review_happy_path_returns_pending(self, client, mock_db_session):
        """A normal profile returns 200 with status='pending' immediately."""
        profile_id = uuid4()
        mock_review = make_review_mock(profile_id=profile_id, status="pending")

        with (
            patch("core.services.review_service.Review", return_value=mock_review),
            patch("api.routes.reviews.process_review", new=AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(profile_id)})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending"
        assert body["profile_id"] == str(profile_id)

    def test_create_review_for_profile_with_no_ingested_documents_returns_pending_200(
        self, client, mock_db_session
    ):
        """Issue #88 regression: a profile with no ingested sources still gets a
        200/"pending" response — create_review performs no document-presence
        validation before creating the review."""
        profile_id = uuid4()
        mock_review = make_review_mock(profile_id=profile_id, status="pending")

        with (
            patch("core.services.review_service.Review", return_value=mock_review),
            patch("api.routes.reviews.process_review", new=AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(profile_id)})

        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_create_review_missing_profile_id_returns_422(self, client):
        """FastAPI request validation still applies to the body shape."""
        response = client.post("/reviews", json={})

        assert response.status_code == 422

    def test_create_review_does_not_validate_profile_existence(self, client, mock_db_session):
        """create_review never queries for the profile, so a nonexistent
        profile_id is accepted the same as a real one — documenting actual
        (unchecked) behavior rather than assuming it 404s."""
        nonexistent_profile_id = uuid4()
        mock_review = make_review_mock(profile_id=nonexistent_profile_id, status="pending")

        with (
            patch("core.services.review_service.Review", return_value=mock_review),
            patch("api.routes.reviews.process_review", new=AsyncMock()),
        ):
            response = client.post("/reviews", json={"profile_id": str(nonexistent_profile_id)})

        assert response.status_code == 200
        mock_db_session.execute.assert_not_called()

    # ---- GET /reviews/{id} ----

    def test_get_review_found_returns_200(self, client, mock_db_session):
        review_id = uuid4()
        mock_review = make_review_mock(id=review_id, status="complete")
        mock_db_session.execute.return_value = make_execute_result(first_return_value=mock_review)

        response = client.get(f"/reviews/{review_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(review_id)

    def test_get_review_not_found_returns_404(self, client, mock_db_session):
        mock_db_session.execute.return_value = make_execute_result(first_return_value=None)

        response = client.get(f"/reviews/{uuid4()}")

        assert response.status_code == 404

    def test_get_review_wrong_owner_returns_404(self, client, mock_db_session):
        """get_review's query joins on Profile.user_id, so a review owned by a
        different user comes back as no rows — same 404 path as not-found."""
        mock_db_session.execute.return_value = make_execute_result(first_return_value=None)

        response = client.get(f"/reviews/{uuid4()}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Review not found"

    # ---- GET /reviews ----

    def test_list_reviews_returns_pagination_metadata(self, client, mock_db_session):
        reviews = [make_review_mock(status="complete") for _ in range(3)]
        mock_db_session.execute.return_value = make_execute_result(all_return_value=reviews)

        response = client.get("/reviews?page=1&page_size=20")

        assert response.status_code == 200
        body = response.json()
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert body["total"] == 3
        assert len(body["items"]) == 3

    def test_list_reviews_invalid_page_size_falls_back_to_default(self, client, mock_db_session):
        mock_db_session.execute.return_value = make_execute_result(all_return_value=[])

        response = client.get("/reviews?page_size=9999")

        assert response.status_code == 200
        assert response.json()["page_size"] == 20

    # ---- GET /reviews/{id}/status ----

    def test_get_review_status_found_returns_status_fields(self, client, mock_db_session):
        review_id = uuid4()
        mock_review = make_review_mock(id=review_id, status="processing")
        mock_db_session.execute.return_value = make_execute_result(first_return_value=mock_review)

        response = client.get(f"/reviews/{review_id}/status")

        assert response.status_code == 200
        body = response.json()
        assert body["review_id"] == str(review_id)
        assert body["status"] == "processing"

    def test_get_review_status_not_found_returns_404(self, client, mock_db_session):
        mock_db_session.execute.return_value = make_execute_result(first_return_value=None)

        response = client.get(f"/reviews/{uuid4()}/status")

        assert response.status_code == 404


@pytest.mark.unit
class TestProcessReviewNoIngestedDocuments:
    """Exercises the background `process_review` pipeline directly (bypassing
    the route) for issue #88's actual gap: a profile with zero ingested
    sources still produces a "complete" review with fabricated feedback."""

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @staticmethod
    def make_profile(**overrides):
        profile = Mock()
        profile.id = overrides.get("id", uuid4())
        profile.github_username = overrides.get("github_username")
        profile.portfolio_url = overrides.get("portfolio_url")
        profile.resume_text = overrides.get("resume_text")
        profile.resume_filename = overrides.get("resume_filename")
        return profile

    @pytest.mark.asyncio
    async def test_no_ingested_documents_still_completes_with_fabricated_feedback(
        self, mock_db_session
    ):
        review_id = uuid4()
        profile_id = uuid4()
        review = make_review_mock(id=review_id, status="pending")
        profile = self.make_profile(id=profile_id)

        mock_db_session.execute.side_effect = [
            make_execute_result(first_return_value=review),
            make_execute_result(first_return_value=profile),
        ]

        await process_review(mock_db_session, review_id, profile_id)

        # This is the actual gap behind issue #88: zero ingested sources still
        # yields a "complete" review with non-empty (fabricated) sections and a
        # score, because the agent/RAG steps ignore ingestion_results entirely.
        assert review.status == "complete"
        assert review.sections is not None
        assert len(review.sections) > 0
        assert review.overall_score is not None

    @pytest.mark.asyncio
    async def test_partial_documents_produces_same_fabricated_output_as_none(self, mock_db_session):
        """Boundary case: a profile with only one source set (github_username)
        goes through the same placeholder agent/RAG steps as a profile with
        zero sources — ingestion_results isn't actually used to distinguish
        "some" documents from "no" documents."""
        review_id = uuid4()
        profile_id = uuid4()
        review = make_review_mock(id=review_id, status="pending")
        profile = self.make_profile(id=profile_id, github_username="octocat")

        mock_db_session.execute.side_effect = [
            make_execute_result(first_return_value=review),
            make_execute_result(first_return_value=profile),
        ]

        await process_review(mock_db_session, review_id, profile_id)

        assert review.status == "complete"
        assert len(review.sections) == 3
        assert review.overall_score == 0.81
