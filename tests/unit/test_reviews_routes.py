"""Tests for reviews.py"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.routes.reviews import _has_ingested_documents, create_review_endpoint, process_review
from api.schemas.review import ReviewCreate


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test suite for create_review_endpoint()."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock authenticated User."""
        user = Mock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def mock_background_tasks(self):
        """Create a mock BackgroundTasks with a spyable add_task."""
        tasks = Mock()
        tasks.add_task = Mock()
        return tasks

    @pytest.fixture
    def review_data(self):
        """Create a ReviewCreate payload for a random profile."""
        return ReviewCreate(profile_id=uuid4())

    def _profile(self, **overrides):
        """Build a mock Profile with all source fields blank unless overridden."""
        defaults = {"github_username": None, "portfolio_url": None, "resume_text": None}
        defaults.update(overrides)
        return Mock(**defaults)

    def _review(self, profile_id):
        """Build a mock Review shaped to satisfy ReviewResponse.model_validate()."""
        now = datetime.utcnow()
        return Mock(
            id=uuid4(),
            profile_id=profile_id,
            status="pending",
            sections=None,
            overall_score=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

    def test_has_ingested_documents_returns_false_when_all_fields_none(self):
        """_has_ingested_documents() should return False when every source field is None."""
        profile = self._profile()
        assert _has_ingested_documents(profile) is False

    def test_has_ingested_documents_returns_false_when_all_fields_whitespace(self):
        """_has_ingested_documents() should treat whitespace-only fields as blank."""
        profile = self._profile(github_username="   ", portfolio_url="\t", resume_text="\n  ")
        assert _has_ingested_documents(profile) is False

    def test_has_ingested_documents_returns_true_when_one_field_populated(self):
        """_has_ingested_documents() should return True if any single field is set."""
        profile = self._profile(github_username="janedoe")
        assert _has_ingested_documents(profile) is True

    @pytest.mark.asyncio
    async def test_create_review_endpoint_raises_400_when_profile_has_no_documents(
        self, mock_db_session, mock_current_user, mock_background_tasks, review_data
    ):
        """create_review_endpoint() should raise 400 when all source fields are None."""
        profile = self._profile()

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=profile)),
            patch("api.routes.reviews.create_review") as mock_create_review,
        ):
            with pytest.raises(
                HTTPException, match="Profile has no ingested documents to review"
            ) as exc_info:
                await create_review_endpoint(
                    data=review_data,
                    background_tasks=mock_background_tasks,
                    current_user=mock_current_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == 400
            mock_create_review.assert_not_called()
            mock_background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_endpoint_raises_400_when_profile_fields_whitespace_only(
        self, mock_db_session, mock_current_user, mock_background_tasks, review_data
    ):
        """create_review_endpoint() should treat whitespace-only fields as no documents."""
        profile = self._profile(github_username="   ", portfolio_url="", resume_text="\n")

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=profile)),
            patch("api.routes.reviews.create_review") as mock_create_review,
        ):
            with pytest.raises(
                HTTPException, match="Profile has no ingested documents to review"
            ) as exc_info:
                await create_review_endpoint(
                    data=review_data,
                    background_tasks=mock_background_tasks,
                    current_user=mock_current_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == 400
            mock_create_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_endpoint_raises_404_when_profile_not_found(
        self, mock_db_session, mock_current_user, mock_background_tasks, review_data
    ):
        """create_review_endpoint() should raise 404, not 400, when the profile doesn't resolve."""
        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=None)),
            patch("api.routes.reviews.create_review") as mock_create_review,
        ):
            with pytest.raises(HTTPException, match="Profile not found") as exc_info:
                await create_review_endpoint(
                    data=review_data,
                    background_tasks=mock_background_tasks,
                    current_user=mock_current_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == 404
            mock_create_review.assert_not_called()
            mock_background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_endpoint_succeeds_when_profile_has_github_username(
        self, mock_db_session, mock_current_user, mock_background_tasks, review_data
    ):
        """create_review_endpoint() should create+schedule a review when a source field is set."""
        profile = self._profile(github_username="janedoe")
        review = self._review(review_data.profile_id)

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=profile)),
            patch(
                "api.routes.reviews.create_review", AsyncMock(return_value=review)
            ) as mock_create_review,
        ):
            result = await create_review_endpoint(
                data=review_data,
                background_tasks=mock_background_tasks,
                current_user=mock_current_user,
                db=mock_db_session,
            )

            assert result.status == "pending"
            mock_create_review.assert_called_once_with(
                db=mock_db_session,
                profile_id=review_data.profile_id,
                user_id=mock_current_user.id,
            )
            mock_background_tasks.add_task.assert_called_once_with(
                process_review, mock_db_session, review.id, review_data.profile_id
            )
