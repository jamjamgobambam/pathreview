"""Tests for review route ownership behavior."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException, status

from api.routes.reviews import create_review_endpoint, process_review
from api.schemas.review import ReviewCreate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_endpoint_rejects_unowned_profile() -> None:
    """Return 404 and skip processing when the user does not own the profile."""
    profile_id = uuid4()
    current_user = Mock(id=str(uuid4()))
    background_tasks = Mock(spec=BackgroundTasks)
    db = AsyncMock()

    with (
        patch(
            "api.routes.reviews.create_review",
            new=AsyncMock(return_value=None),
        ) as mock_create_review,
        pytest.raises(HTTPException) as exc_info,
    ):
        await create_review_endpoint(
            data=ReviewCreate(profile_id=profile_id),
            background_tasks=background_tasks,
            current_user=current_user,
            db=db,
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Profile not found"
    mock_create_review.assert_awaited_once_with(
        db=db,
        profile_id=profile_id,
        user_id=current_user.id,
    )
    background_tasks.add_task.assert_not_called()
    db.rollback.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_endpoint_processes_owned_profile() -> None:
    """Return the review and schedule processing for an owned profile."""
    profile_id = uuid4()
    review_id = uuid4()
    now = datetime.now(UTC)
    current_user = Mock(id=str(uuid4()))
    background_tasks = Mock(spec=BackgroundTasks)
    db = AsyncMock()
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
        response = await create_review_endpoint(
            data=ReviewCreate(profile_id=profile_id),
            background_tasks=background_tasks,
            current_user=current_user,
            db=db,
        )

    assert response.id == review_id
    assert response.profile_id == profile_id
    assert response.status == "pending"
    background_tasks.add_task.assert_called_once_with(
        process_review,
        db,
        review_id,
        profile_id,
    )
