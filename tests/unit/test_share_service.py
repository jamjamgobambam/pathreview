"""Tests for share_service.py"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from core.services.share_service import (
    ReviewNotFoundError,
    ReviewNotShareableError,
    create_share_link,
    get_shared_review,
)


@pytest.mark.unit
class TestShareService:
    """Test suite for share_service module."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @staticmethod
    def _result(first_value):
        """Build a mock execute() result whose scalars().first() returns a value.

        The result itself is a synchronous Mock (only ``execute`` is awaited), so
        ``result.scalars().first()`` resolves without an ``await`` regardless of
        the local Python/AsyncMock version.
        """
        result = Mock()
        result.scalars.return_value.first.return_value = first_value
        return result

    # ---- create_share_link ----

    @pytest.mark.asyncio
    async def test_create_share_link_mints_new_link_when_none_exists(self, mock_db_session):
        """A completed review with no existing link gets a fresh token + 30-day expiry."""
        review_id = uuid4()
        user_id = str(uuid4())

        review = Mock()
        review.status = "complete"

        # First execute: review lookup. Second execute: existing-link lookup (none).
        mock_db_session.execute = AsyncMock(side_effect=[self._result(review), self._result(None)])

        before = datetime.now(UTC)
        share_link = await create_share_link(mock_db_session, review_id, user_id)
        after = datetime.now(UTC)

        assert isinstance(share_link.token, str)
        assert len(share_link.token) >= 32
        assert share_link.review_id == review_id
        # Expiry is roughly 30 days out.
        assert before + timedelta(days=30) <= share_link.expires_at <= after + timedelta(days=30)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_share_link_reuses_existing_unexpired_link(self, mock_db_session):
        """If an unexpired link already exists, it is reused (no new row)."""
        review_id = uuid4()
        user_id = str(uuid4())

        review = Mock()
        review.status = "complete"

        existing = Mock()
        existing.token = "existing-token"

        mock_db_session.execute = AsyncMock(
            side_effect=[self._result(review), self._result(existing)]
        )

        share_link = await create_share_link(mock_db_session, review_id, user_id)

        assert share_link is existing
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_link_raises_when_review_not_found(self, mock_db_session):
        """A review that doesn't exist / isn't owned by the user raises ReviewNotFoundError."""
        review_id = uuid4()
        user_id = str(uuid4())

        mock_db_session.execute = AsyncMock(side_effect=[self._result(None)])

        with pytest.raises(ReviewNotFoundError):
            await create_share_link(mock_db_session, review_id, user_id)

        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_link_raises_when_review_not_complete(self, mock_db_session):
        """A review that isn't complete raises ReviewNotShareableError."""
        review_id = uuid4()
        user_id = str(uuid4())

        review = Mock()
        review.status = "processing"

        mock_db_session.execute = AsyncMock(side_effect=[self._result(review)])

        with pytest.raises(ReviewNotShareableError):
            await create_share_link(mock_db_session, review_id, user_id)

        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_link_generates_unique_tokens(self, mock_db_session):
        """Two mint operations produce different tokens."""
        review_id = uuid4()
        user_id = str(uuid4())

        review = Mock()
        review.status = "complete"

        mock_db_session.execute = AsyncMock(
            side_effect=[
                self._result(review),
                self._result(None),
                self._result(review),
                self._result(None),
            ]
        )

        first = await create_share_link(mock_db_session, review_id, user_id)
        second = await create_share_link(mock_db_session, review_id, user_id)

        assert first.token != second.token

    # ---- get_shared_review ----

    @pytest.mark.asyncio
    async def test_get_shared_review_returns_link_when_valid(self, mock_db_session):
        """A known, unexpired token resolves to its share link."""
        share_link = Mock()
        share_link.expires_at = datetime.now(UTC) + timedelta(days=1)

        mock_db_session.execute = AsyncMock(return_value=self._result(share_link))

        result = await get_shared_review(mock_db_session, "some-token")

        assert result is share_link

    @pytest.mark.asyncio
    async def test_get_shared_review_returns_none_when_expired(self, mock_db_session):
        """An expired token resolves to None (link no longer valid)."""
        share_link = Mock()
        share_link.expires_at = datetime.now(UTC) - timedelta(days=1)

        mock_db_session.execute = AsyncMock(return_value=self._result(share_link))

        result = await get_shared_review(mock_db_session, "expired-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_shared_review_returns_none_when_token_unknown(self, mock_db_session):
        """An unknown token resolves to None."""
        mock_db_session.execute = AsyncMock(return_value=self._result(None))

        result = await get_shared_review(mock_db_session, "nonexistent-token")

        assert result is None
