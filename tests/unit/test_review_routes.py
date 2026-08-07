"""Tests for the review API routes."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException, status

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_rejects_profile_without_ingested_documents() -> None:
    """Return a controlled error when a profile has no ingested documents."""
    profile_id = uuid4()
    current_user = SimpleNamespace(id=str(uuid4()))
    profile = SimpleNamespace(id=profile_id, user_id=current_user.id)

    profile_result = Mock()
    profile_result.scalars.return_value.first.return_value = profile
    source_result = Mock()
    source_result.scalars.return_value.first.return_value = None

    db = AsyncMock()
    db.execute.side_effect = [profile_result, source_result]
    background_tasks = BackgroundTasks()

    with (
        patch("api.routes.reviews.create_review", new_callable=AsyncMock) as create_review,
        patch("api.routes.reviews.process_review", new_callable=AsyncMock),
        pytest.raises(HTTPException) as exc_info,
    ):
        await create_review_endpoint(
            data=ReviewCreate(profile_id=profile_id),
            background_tasks=background_tasks,
            current_user=current_user,
            db=db,
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Profile has no ingested documents"
    create_review.assert_not_awaited()
    db.commit.assert_not_awaited()
    assert background_tasks.tasks == []
