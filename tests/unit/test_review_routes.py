"""Unit tests for review routes."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from api.routes.reviews import create_review_endpoint, process_review
from api.schemas.review import ReviewCreate


class TestCreateReviewEndpointNoIngestedDocuments:
    """Tests for POST /reviews when a profile has no ingested documents."""

    @pytest.mark.asyncio
    async def test_create_review_returns_pending_for_profile_with_no_documents(
        self,
    ) -> None:
        """A documentless profile should still receive a pending review."""
        profile_id = uuid4()
        user_id = uuid4()
        review_id = uuid4()
        now = datetime.now(UTC)

        data = ReviewCreate(profile_id=profile_id)

        current_user = Mock()
        current_user.id = user_id

        db = AsyncMock()
        background_tasks = BackgroundTasks()

        pending_review = SimpleNamespace(
            id=review_id,
            profile_id=profile_id,
            status="pending",
            sections=None,
            overall_score=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        with patch(
            "api.routes.reviews.create_review",
            new=AsyncMock(return_value=pending_review),
        ) as mock_create_review:
            response = await create_review_endpoint(
                data=data,
                background_tasks=background_tasks,
                current_user=current_user,
                db=db,
            )

        assert response.id == review_id
        assert response.profile_id == profile_id
        assert response.status == "pending"
        assert response.sections is None
        assert response.overall_score is None

        mock_create_review.assert_awaited_once_with(
            db=db,
            profile_id=profile_id,
            user_id=user_id,
        )

    @pytest.mark.asyncio
    async def test_create_review_schedules_processing_for_profile_with_no_documents(
        self,
    ) -> None:
        """A documentless profile should still schedule review processing."""
        profile_id = uuid4()
        user_id = uuid4()
        review_id = uuid4()
        now = datetime.now(UTC)

        data = ReviewCreate(profile_id=profile_id)

        current_user = Mock()
        current_user.id = user_id

        db = AsyncMock()
        background_tasks = BackgroundTasks()

        pending_review = SimpleNamespace(
            id=review_id,
            profile_id=profile_id,
            status="pending",
            sections=None,
            overall_score=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        with patch(
            "api.routes.reviews.create_review",
            new=AsyncMock(return_value=pending_review),
        ):
            await create_review_endpoint(
                data=data,
                background_tasks=background_tasks,
                current_user=current_user,
                db=db,
            )

        assert len(background_tasks.tasks) == 1

        scheduled_task = background_tasks.tasks[0]
        assert scheduled_task.func is process_review
        assert scheduled_task.args == (db, review_id, profile_id)

    @pytest.mark.asyncio
    async def test_create_review_returns_500_when_service_fails(
        self,
    ) -> None:
        """Unexpected review creation failures should return a 500 error."""
        profile_id = uuid4()

        data = ReviewCreate(profile_id=profile_id)

        current_user = Mock()
        current_user.id = uuid4()

        db = AsyncMock()
        background_tasks = BackgroundTasks()

        with (
            patch(
                "api.routes.reviews.create_review",
                new=AsyncMock(side_effect=RuntimeError("database unavailable")),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_review_endpoint(
                data=data,
                background_tasks=background_tasks,
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Failed to create review"
        db.rollback.assert_awaited_once()
        assert len(background_tasks.tasks) == 0
