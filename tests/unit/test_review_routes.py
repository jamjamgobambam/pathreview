"""Tests for review creation route authorization behavior."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


@pytest.mark.unit
class TestCreateReviewEndpoint:
    """Test review creation endpoint ownership handling."""

    @pytest.mark.asyncio
    async def test_unowned_profile_returns_404_without_background_task(self):
        """Reject an unowned profile before scheduling review processing."""
        profile_id = uuid4()
        current_user = SimpleNamespace(id=uuid4())
        background_tasks = BackgroundTasks()
        db = AsyncMock()

        with (
            patch("api.routes.reviews.create_review", new=AsyncMock(return_value=None)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_review_endpoint(
                data=ReviewCreate(profile_id=profile_id),
                background_tasks=background_tasks,
                current_user=current_user,
                db=db,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Profile not found"
        assert background_tasks.tasks == []
        db.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_owned_profile_schedules_background_task(self):
        """Create a pending review and schedule processing for its owner."""
        profile_id = uuid4()
        review_id = uuid4()
        current_user = SimpleNamespace(id=uuid4())
        background_tasks = BackgroundTasks()
        db = AsyncMock()
        now = datetime.now(UTC)
        review = SimpleNamespace(
            id=review_id,
            profile_id=profile_id,
            status="pending",
            sections=None,
            overall_score=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        create_mock = AsyncMock(return_value=review)
        with patch("api.routes.reviews.create_review", new=create_mock):
            response = await create_review_endpoint(
                data=ReviewCreate(profile_id=profile_id),
                background_tasks=background_tasks,
                current_user=current_user,
                db=db,
            )

        assert response.id == review_id
        assert response.status == "pending"
        create_mock.assert_awaited_once_with(
            db=db,
            profile_id=profile_id,
            user_id=current_user.id,
        )
        assert len(background_tasks.tasks) == 1
        db.rollback.assert_not_awaited()
