"""Tests for share_service.py"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy import Delete

import core.services.share_service as share_service
from core.services.share_service import (
    SHARE_LINK_TTL,
    ShareLinkExpiredError,
    build_share_url,
    create_share_link,
    get_review_by_share_token,
)


def _query_result(first: object = None) -> Mock:
    """Build a mock that mimics ``(await db.execute(...)).scalars().first()``.

    ``db.execute`` is awaited (AsyncMock), but ``.scalars().first()`` is called
    synchronously, so the result itself must be a plain Mock, not an AsyncMock.
    """
    result = Mock()
    result.scalars.return_value.first.return_value = first
    return result


@pytest.mark.unit
class TestShareService:
    """Test suite for share_service module."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock async database session."""
        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    # ---- build_share_url -------------------------------------------------

    def test_build_share_url_formats_token(self) -> None:
        """build_share_url points at the frontend /shared/<token> route."""
        assert build_share_url("abc123") == "http://localhost:5173/shared/abc123"

    def test_build_share_url_strips_trailing_slash(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A trailing slash on the base URL does not produce a double slash."""
        monkeypatch.setattr(share_service.settings, "frontend_base_url", "http://example.com/")
        assert build_share_url("tok") == "http://example.com/shared/tok"

    # ---- create_share_link ----------------------------------------------

    @pytest.mark.asyncio
    async def test_create_share_link_returns_none_when_not_owned(self, mock_db: AsyncMock) -> None:
        """Returns None (caller -> 404) when the review isn't owned by the user."""
        mock_db.execute = AsyncMock(side_effect=[_query_result(first=None)])

        result = await create_share_link(mock_db, review_id=uuid4(), user_id=uuid4())

        assert result is None
        # No link minted or persisted for a non-owner.
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_link_reuses_existing_valid_link(self, mock_db: AsyncMock) -> None:
        """Re-clicking Share returns the existing non-expired link, not a new one."""
        review_id = uuid4()
        existing = Mock()
        existing.token = "existing-token"
        # 1) ownership check, 2) delete expired, 3) existing-link lookup
        mock_db.execute = AsyncMock(
            side_effect=[
                _query_result(first=review_id),
                _query_result(),
                _query_result(first=existing),
            ]
        )

        result = await create_share_link(mock_db, review_id=review_id, user_id=uuid4())

        assert result is existing
        mock_db.add.assert_not_called()  # no duplicate minted
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_share_link_mints_new_when_none_exists(self, mock_db: AsyncMock) -> None:
        """Mints a fresh link when the review has no valid link yet."""
        review_id = uuid4()
        mock_db.execute = AsyncMock(
            side_effect=[
                _query_result(first=review_id),  # ownership
                _query_result(),  # delete expired
                _query_result(first=None),  # no existing valid link
            ]
        )

        result = await create_share_link(mock_db, review_id=review_id, user_id=uuid4())

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

        minted = mock_db.add.call_args[0][0]
        assert result is not None
        assert result is minted
        assert result.review_id == review_id
        # secrets.token_urlsafe(32) yields a 43-char opaque string.
        assert len(result.token) == 43
        # Expiry is ~30 days out and timezone-aware.
        assert result.expires_at.tzinfo is not None
        delta = result.expires_at - datetime.now(UTC)
        assert abs(delta - SHARE_LINK_TTL) < timedelta(seconds=10)

    @pytest.mark.asyncio
    async def test_create_share_link_deletes_expired_before_minting(
        self, mock_db: AsyncMock
    ) -> None:
        """Expired rows for the review are deleted before a new link is minted."""
        review_id = uuid4()
        mock_db.execute = AsyncMock(
            side_effect=[
                _query_result(first=review_id),
                _query_result(),
                _query_result(first=None),
            ]
        )

        await create_share_link(mock_db, review_id=review_id, user_id=uuid4())

        # The second execute() is the cleanup DELETE.
        second_stmt = mock_db.execute.call_args_list[1].args[0]
        assert isinstance(second_stmt, Delete)

    @pytest.mark.asyncio
    async def test_create_share_link_mints_unique_tokens(self, mock_db: AsyncMock) -> None:
        """Two freshly minted links get different tokens."""
        review_id = uuid4()
        side_effects = [
            _query_result(first=review_id),
            _query_result(),
            _query_result(first=None),
        ] * 2
        mock_db.execute = AsyncMock(side_effect=side_effects)

        first = await create_share_link(mock_db, review_id=review_id, user_id=uuid4())
        second = await create_share_link(mock_db, review_id=review_id, user_id=uuid4())

        assert first is not None and second is not None
        assert first.token != second.token

    # ---- get_review_by_share_token --------------------------------------

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_none_for_unknown(
        self, mock_db: AsyncMock
    ) -> None:
        """An unknown token resolves to None (caller -> 404)."""
        mock_db.execute = AsyncMock(side_effect=[_query_result(first=None)])

        result = await get_review_by_share_token(mock_db, token="does-not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_raises_for_expired(self, mock_db: AsyncMock) -> None:
        """An expired token raises ShareLinkExpiredError (caller -> 410)."""
        expired_link = Mock()
        expired_link.review_id = uuid4()
        expired_link.expires_at = datetime.now(UTC) - timedelta(days=1)
        mock_db.execute = AsyncMock(side_effect=[_query_result(first=expired_link)])

        with pytest.raises(ShareLinkExpiredError):
            await get_review_by_share_token(mock_db, token="expired-token")

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_review_when_valid(
        self, mock_db: AsyncMock
    ) -> None:
        """A valid, unexpired token resolves to its review."""
        valid_link = Mock()
        valid_link.review_id = uuid4()
        valid_link.expires_at = datetime.now(UTC) + timedelta(days=1)
        review = Mock()
        # 1) token lookup, 2) review lookup
        mock_db.execute = AsyncMock(
            side_effect=[_query_result(first=valid_link), _query_result(first=review)]
        )

        result = await get_review_by_share_token(mock_db, token="valid-token")

        assert result is review
