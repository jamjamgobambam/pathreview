"""Regression tests for review profile ownership."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import create_review


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_review_rejects_profile_owned_by_another_user() -> None:
    """Reproduce issue #163: review creation must enforce profile ownership."""
    # Use different IDs to represent a logged-in user requesting a review for
    # a profile that they do not own.
    profile_id = uuid4()
    authenticated_user_id = uuid4()

    # Mock the database so the test only checks the service's ownership logic.
    db = AsyncMock()
    db.add = Mock()

    # A correct query filters by both profile_id and authenticated_user_id.
    # Returning None means no profile belongs to this user with that ID.
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_result

    # Patch Review so we can verify that an unauthorized review is never built.
    with patch("core.services.review_service.Review") as mock_review_model:
        result = await create_review(
            db,
            profile_id,
            authenticated_user_id,
        )

    # Expected safe behavior: return None after one ownership query and perform
    # no review creation or database writes. The first assertion currently
    # fails because create_review() ignores authenticated_user_id.
    assert result is None
    db.execute.assert_awaited_once()
    mock_review_model.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
