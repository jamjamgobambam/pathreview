"""Tests for share_service.py - public review link generation.

These tests test expected functionality of the shareable link feature.
A new share_token and share_token_expires_at field are added as columns on Review model.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from core.services.share_service import (  # type: ignore[import-not-found]
    create_share_link,
    get_public_review,
)


@pytest.mark.unit
class TestCreateShareLink:
    """Tests for create_share_link(db, review_id, user_id) -> Review.

    The service sets review.share_token and review.share_token_expires_at on the
    existing Review row and commits. Returns the updated Review.
    """

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def review_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def user_id(self) -> UUID:
        return uuid4()

    def _make_review(
        self,
        review_id: UUID,
        user_id: UUID,
        share_token: str | None = None,
        share_token_expires_at: datetime | None = None,
    ) -> Mock:
        review = Mock()
        review.id = review_id
        review.user_id = user_id
        review.status = "complete"
        review.share_token = share_token
        review.share_token_expires_at = share_token_expires_at
        return review

    def _setup_db(self, mock_db_session: AsyncMock, review: Mock | None) -> None:
        """Single execute: ownership-checked query returns the Review (or None)."""
        result = Mock()
        result.scalars.return_value.first.return_value = review
        mock_db_session.execute.return_value = result

    @pytest.mark.asyncio
    async def test_returns_new_token_when_no_active_link_exists(
        self, mock_db_session: AsyncMock, review_id: UUID, user_id: UUID
    ) -> None:
        """Happy path: no share_token on review — generates a new one and returns the review."""
        review = self._make_review(review_id, user_id, share_token=None)
        self._setup_db(mock_db_session, review)

        result = await create_share_link(mock_db_session, review_id, user_id)

        assert result is not None
        assert result.share_token is not None
        assert len(result.share_token) > 0

    @pytest.mark.asyncio
    async def test_returns_existing_token_when_active_link_exists(
        self, mock_db_session: AsyncMock, review_id: UUID, user_id: UUID
    ) -> None:
        """Idempotent: valid share_token already present — returns it without writing to db."""
        future_expiry = datetime.now(UTC) + timedelta(days=20)
        review = self._make_review(
            review_id,
            user_id,
            share_token="already-active-token",
            share_token_expires_at=future_expiry,
        )
        self._setup_db(mock_db_session, review)

        result = await create_share_link(mock_db_session, review_id, user_id)

        assert result.share_token == "already-active-token"
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_token_when_existing_link_is_expired(
        self, mock_db_session: AsyncMock, review_id: UUID, user_id: UUID
    ) -> None:
        """Expired token is replaced: new share_token is set on the review and committed."""
        past_expiry = datetime.now(UTC) - timedelta(days=1)
        review = self._make_review(
            review_id,
            user_id,
            share_token="old-expired-token",
            share_token_expires_at=past_expiry,
        )
        self._setup_db(mock_db_session, review)

        result = await create_share_link(mock_db_session, review_id, user_id)

        assert result.share_token != "old-expired-token"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_commits_but_does_not_add_when_creating_new_token(
        self, mock_db_session: AsyncMock, review_id: UUID, user_id: UUID
    ) -> None:
        """Updating a column on an existing row uses commit, not db.add (no new row inserted)."""
        review = self._make_review(review_id, user_id, share_token=None)
        self._setup_db(mock_db_session, review)

        await create_share_link(mock_db_session, review_id, user_id)

        mock_db_session.commit.assert_called_once()
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_new_token_expires_in_30_days(
        self, mock_db_session: AsyncMock, review_id: UUID, user_id: UUID
    ) -> None:
        """review.share_token_expires_at is set to exactly 30 days from creation time."""
        review = self._make_review(review_id, user_id, share_token=None)
        self._setup_db(mock_db_session, review)

        fixed_now = datetime(2026, 1, 1, tzinfo=UTC)
        expected_expiry = datetime(2026, 1, 31, tzinfo=UTC)

        with patch("core.services.share_service.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            await create_share_link(mock_db_session, review_id, user_id)

        assert review.share_token_expires_at == expected_expiry

    @pytest.mark.asyncio
    async def test_raises_when_review_not_owned_by_user(
        self, mock_db_session: AsyncMock, review_id: UUID
    ) -> None:
        """Non-owner or missing review raises ValueError."""
        self._setup_db(mock_db_session, review=None)

        with pytest.raises(ValueError):
            await create_share_link(mock_db_session, review_id, uuid4())


@pytest.mark.unit
class TestGetPublicReview:
    """Tests for get_public_review(db, token) -> Review.

    Queries the Review table by share_token column. No authentication required.
    """

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def review_id(self) -> UUID:
        return uuid4()

    def _setup_db(self, mock_db_session: AsyncMock, review: Mock | None) -> None:
        """Single execute: query Review by share_token."""
        result = Mock()
        result.scalars.return_value.first.return_value = review
        mock_db_session.execute.return_value = result

    def _make_shared_review(
        self, review_id: UUID, expires_at: datetime, token: str = "valid-token"
    ) -> Mock:
        review = Mock()
        review.id = review_id
        review.status = "complete"
        review.sections = []
        review.overall_score = 0.8
        review.share_token = token
        review.share_token_expires_at = expires_at
        return review

    @pytest.mark.asyncio
    async def test_returns_review_for_valid_non_expired_token(
        self, mock_db_session: AsyncMock, review_id: UUID
    ) -> None:
        """Happy path: valid non-expired share_token returns the review."""
        future_expiry = datetime.now(UTC) + timedelta(days=15)
        review = self._make_shared_review(review_id, expires_at=future_expiry)
        self._setup_db(mock_db_session, review)

        result = await get_public_review(mock_db_session, "valid-token")

        assert result is not None
        assert result.id == review_id

    @pytest.mark.asyncio
    async def test_raises_for_expired_token(
        self, mock_db_session: AsyncMock, review_id: UUID
    ) -> None:
        """Token past share_token_expires_at is rejected — link inaccessible after 30 days."""
        past_expiry = datetime.now(UTC) - timedelta(seconds=1)
        review = self._make_shared_review(review_id, expires_at=past_expiry, token="expired-token")
        self._setup_db(mock_db_session, review)

        with pytest.raises(ValueError):
            await get_public_review(mock_db_session, "expired-token")

    @pytest.mark.asyncio
    async def test_raises_for_nonexistent_token(self, mock_db_session: AsyncMock) -> None:
        """Token not found in the Review table raises LookupError."""
        self._setup_db(mock_db_session, review=None)

        with pytest.raises(LookupError):
            await get_public_review(mock_db_session, "does-not-exist")

    @pytest.mark.asyncio
    async def test_token_expiry_at_exact_boundary(
        self, mock_db_session: AsyncMock, review_id: UUID
    ) -> None:
        """Token expiring at exactly 'now' is treated as expired (boundary check)."""
        exact_now = datetime.now(UTC)
        review = self._make_shared_review(review_id, expires_at=exact_now, token="boundary-token")
        self._setup_db(mock_db_session, review)

        with pytest.raises(ValueError):
            await get_public_review(mock_db_session, "boundary-token")

    @pytest.mark.asyncio
    async def test_function_signature_requires_no_user_id(self) -> None:
        """get_public_review must not require user_id — it is an unauthenticated endpoint."""
        import inspect

        sig = inspect.signature(get_public_review)
        assert (
            "user_id" not in sig.parameters
        ), "get_public_review must not accept user_id — public links are accessed without auth"
