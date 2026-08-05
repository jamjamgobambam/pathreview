"""Tests for api/routes/reviews.py"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test suite for POST /reviews (create_review_endpoint)."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_user(self) -> Mock:
        user = Mock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def mock_profile(self) -> Mock:
        profile = Mock()
        profile.id = uuid4()
        return profile

    @pytest.mark.asyncio
    async def test_returns_400_for_profile_with_no_ingested_documents(
        self,
        mock_db_session: AsyncMock,
        mock_user: Mock,
        mock_profile: Mock,
    ) -> None:
        """
        Issue #88: POST /reviews should reject requests for a profile with no
        ingested documents (no github_username/portfolio_url/resume_text and
        no IngestedSource rows) with a clear 400, rather than creating a
        review that later fabricates content.
        """
        mock_profile.github_username = None
        mock_profile.portfolio_url = None
        mock_profile.resume_text = None

        data = ReviewCreate(profile_id=mock_profile.id)
        background_tasks = BackgroundTasks()

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=mock_profile)),
            patch(
                "api.routes.reviews.profile_has_ingested_content",
                AsyncMock(return_value=False),
            ),
            patch("api.routes.reviews.create_review") as mock_create_review,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_review_endpoint(
                    data=data,
                    background_tasks=background_tasks,
                    current_user=mock_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == 400
            mock_create_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_profile(
        self,
        mock_db_session: AsyncMock,
        mock_user: Mock,
    ) -> None:
        """A profile_id that doesn't exist (or isn't owned by the user) should 404."""
        data = ReviewCreate(profile_id=uuid4())
        background_tasks = BackgroundTasks()

        with patch("api.routes.reviews.get_profile", AsyncMock(return_value=None)):
            with pytest.raises(HTTPException) as exc_info:
                await create_review_endpoint(
                    data=data,
                    background_tasks=background_tasks,
                    current_user=mock_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_creates_review_for_profile_with_ingested_content(
        self,
        mock_db_session: AsyncMock,
        mock_user: Mock,
        mock_profile: Mock,
    ) -> None:
        """A profile with content should still create a pending review as before."""
        mock_profile.github_username = "octocat"
        mock_profile.portfolio_url = None
        mock_profile.resume_text = None

        data = ReviewCreate(profile_id=mock_profile.id)
        background_tasks = BackgroundTasks()

        mock_review = Mock()
        mock_review.id = uuid4()
        mock_review.profile_id = mock_profile.id
        mock_review.status = "pending"
        mock_review.sections = None
        mock_review.overall_score = None
        mock_review.error_message = None
        mock_review.created_at = datetime.utcnow()
        mock_review.updated_at = datetime.utcnow()

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=mock_profile)),
            patch(
                "api.routes.reviews.profile_has_ingested_content",
                AsyncMock(return_value=True),
            ),
            patch(
                "api.routes.reviews.create_review",
                AsyncMock(return_value=mock_review),
            ) as mock_create_review,
        ):
            result = await create_review_endpoint(
                data=data,
                background_tasks=background_tasks,
                current_user=mock_user,
                db=mock_db_session,
            )

            mock_create_review.assert_called_once()
            assert result.status == "pending"
