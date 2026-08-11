"""Tests for review_routes.py"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from api.routes.reviews import create_review_endpoint


@pytest.mark.unit
class TestReviewRoutes:
    """Test suite for the reviews route module."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_profile_no_ingested_docs(self, mock_db_session: AsyncMock) -> None:
        current_user = Mock()
        current_user.id = uuid4()
        data = Mock()
        data.profile_id = uuid4()
        background_tasks = Mock()
        background_tasks.add_task = Mock()
        with patch(
            "api.routes.reviews.create_review",
            new_callable=AsyncMock,
        ) as mock_create_review:
            mock_create_review.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ingested documents available",
            )

            with pytest.raises(HTTPException) as exc_info:
                await create_review_endpoint(
                    data=data,
                    background_tasks=background_tasks,
                    current_user=current_user,
                    db=mock_db_session,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == "No ingested documents available"
            mock_create_review.assert_awaited_once_with(
                db=mock_db_session,
                profile_id=data.profile_id,
                user_id=current_user.id,
            )
            background_tasks.add_task.assert_not_called()
