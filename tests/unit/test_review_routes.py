"""Tests for review API routes."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_endpoint_rejects_unowned_profile() -> None:
    """Return 404 and skip processing when the service rejects profile ownership."""
    profile_id = uuid4()
    data = ReviewCreate(profile_id=profile_id)
    background_tasks = Mock()
    current_user = Mock(id=uuid4())
    db = AsyncMock()

    with (
        patch(
            "api.routes.reviews.create_review",
            new=AsyncMock(return_value=None),
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await create_review_endpoint(data, background_tasks, current_user, db)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Profile not found"
    background_tasks.add_task.assert_not_called()
