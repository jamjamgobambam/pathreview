"""Tests for api/routes/reviews.py"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test suite for create_review_endpoint."""

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_current_user(self):
        user = Mock()
        user.id = uuid4()
        return user

    @pytest.fixture
    def mock_background_tasks(self):
        tasks = Mock()
        tasks.add_task = Mock()
        return tasks

    @pytest.mark.asyncio
    async def test_returns_400_when_profile_has_no_ingested_sources(
        self, mock_db_session, mock_current_user, mock_background_tasks
    ):
        """Endpoint should reject with 400 and not create a review or schedule processing."""
        data = ReviewCreate(profile_id=uuid4())

        with (
            patch("api.routes.reviews.check_has_ingested_sources", AsyncMock(return_value=False)),
            patch("api.routes.reviews.create_review", AsyncMock()) as mock_create_review,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_review_endpoint(
                    data=data,
                    background_tasks=mock_background_tasks,
                    current_user=mock_current_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Profile has no ingested content"
            mock_create_review.assert_not_called()
            mock_background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_pending_review_when_profile_has_ingested_sources(
        self, mock_db_session, mock_current_user, mock_background_tasks
    ):
        """Happy path: profile with at least one ingested source still creates a pending review."""
        data = ReviewCreate(profile_id=uuid4())

        mock_review = Mock()
        mock_review.id = uuid4()
        mock_review.profile_id = data.profile_id
        mock_review.status = "pending"
        mock_review.sections = None
        mock_review.overall_score = None
        mock_review.error_message = None
        mock_review.created_at = datetime.utcnow()
        mock_review.updated_at = datetime.utcnow()

        with (
            patch("api.routes.reviews.check_has_ingested_sources", AsyncMock(return_value=True)),
            patch(
                "api.routes.reviews.create_review", AsyncMock(return_value=mock_review)
            ) as mock_create_review,
        ):
            response = await create_review_endpoint(
                data=data,
                background_tasks=mock_background_tasks,
                current_user=mock_current_user,
                db=mock_db_session,
            )

            assert response.status == "pending"
            mock_create_review.assert_called_once_with(
                db=mock_db_session,
                profile_id=data.profile_id,
                user_id=mock_current_user.id,
            )
            mock_background_tasks.add_task.assert_called_once()
