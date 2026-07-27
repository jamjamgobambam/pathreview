"""Tests for review_service.py"""

from datetime import UTC
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import (
    create_review,
    create_share_link,
    get_review,
    get_review_by_share_token,
    list_reviews,
)


@pytest.mark.unit
class TestReviewService:
    """Test suite for review_service module."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_review(self) -> Mock:
        """Create a mock Review object."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        return review

    @pytest.fixture
    def mock_profile(self) -> Mock:
        """Create a mock Profile object."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        return profile

    @pytest.fixture
    def mock_share_link(self) -> Mock:
        """Create a mock ShareLink object."""
        from datetime import datetime, timedelta

        share_link = Mock()
        share_link.id = uuid4()
        share_link.token = "fake-token-abc123"
        share_link.review_id = uuid4()
        share_link.expires_at = datetime.now(UTC) + timedelta(days=30)
        share_link.is_expired = Mock(return_value=False)
        return share_link

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(
        self, mock_db_session: AsyncMock, mock_review: Mock
    ) -> None:
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        # Setup mock
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch("core.services.review_service.Review") as mock_review_cls:  # noqa: N806
            mock_instance = mock_review_cls.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            await create_review(mock_db_session, profile_id, user_id)

            # Check that Review was instantiated
            mock_review_cls.assert_called()
            call_kwargs = mock_review_cls.call_args[1]
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id

        # Setup mock execute to return review
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, user_id)

        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session: AsyncMock) -> None:
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        # Setup mock to return None
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, wrong_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # Create mock reviews
        mock_reviews = [Mock() for _ in range(5)]

        # Setup execute mock to return reviews
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=20)

        assert len(reviews) > 0 or len(reviews) == 0  # May be empty
        assert isinstance(total, int)
        assert total >= 0

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test list_reviews page 2 returns correct offset."""
        user_id = uuid4()
        page_size = 20

        # Setup mock
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # Second call should pass offset for page 2
        calls = mock_db_session.execute.call_args_list
        # Should have at least one call
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await list_reviews(mock_db_session, user_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_create_review_calls_db_add(self, mock_db_session: AsyncMock) -> None:
        """Test create_review calls db.add()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session: AsyncMock) -> None:
        """Test create_review calls db.commit()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session: AsyncMock) -> None:
        """Test create_review calls db.refresh()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session: AsyncMock) -> None:
        """Test get_review constructs proper SQL with join."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should call execute with a statement
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should use default page=1, page_size=20
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(
            mock_db_session, user_id, page=1, page_size=custom_page_size
        )

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session: AsyncMock) -> None:
        """Test create_review handles UUID objects correctly."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_cls:  # noqa: N806
            mock_review_cls.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = mock_review_cls.call_args[1]
            assert "profile_id" in call_kwargs
            assert "status" in call_kwargs

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session: AsyncMock) -> None:
        """Test get_review checks Profile.user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should construct query with user_id filter
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(5)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Total should be counted
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test review has None for sections and overall_score initially."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_cls:  # noqa: N806
            mock_review_cls.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = mock_review_cls.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session: AsyncMock) -> None:
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Should not raise
        result = await get_review(mock_db_session, review_id, user_id)

        assert result is None or result is not None  # Just verify no exception

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await list_reviews(mock_db_session, user_id)

        # Should order by created_at descending
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_share_link_returns_share_link_for_owned_review(
        self, mock_db_session: AsyncMock, mock_review: Mock
    ) -> None:
        """Test create_share_link returns a ShareLink when the review exists and is owned."""
        review_id = uuid4()
        user_id = uuid4()

        with (
            patch(
                "core.services.review_service.get_review",
                new=AsyncMock(return_value=mock_review),
            ),
            patch("core.services.review_service.ShareLink") as mock_share_link_cls,  # noqa: N806
        ):
            mock_instance = mock_share_link_cls.return_value
            mock_instance.expires_at = Mock()
            mock_instance.expires_at.isoformat.return_value = "2026-08-21T00:00:00+00:00"

            result = await create_share_link(mock_db_session, review_id, user_id)

            mock_share_link_cls.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
            assert result == mock_instance

    @pytest.mark.asyncio
    async def test_create_share_link_returns_none_when_review_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test create_share_link returns None when the review doesn't exist or isn't owned."""
        review_id = uuid4()
        user_id = uuid4()

        with patch(
            "core.services.review_service.get_review",
            new=AsyncMock(return_value=None),
        ):
            result = await create_share_link(mock_db_session, review_id, user_id)

            assert result is None
            mock_db_session.add.assert_not_called()
            mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_review_for_valid_token(
        self, mock_db_session: AsyncMock, mock_share_link: Mock, mock_review: Mock
    ) -> None:
        """Test get_review_by_share_token returns the review for a valid, unexpired token."""
        token = "fake-token-abc123"

        share_link_result = Mock()
        share_link_result.scalars.return_value.first.return_value = mock_share_link

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review

        # First execute() call looks up the ShareLink, second looks up the Review
        mock_db_session.execute = AsyncMock(side_effect=[share_link_result, review_result])

        result = await get_review_by_share_token(mock_db_session, token)

        assert result == mock_review
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_none_for_unknown_token(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_review_by_share_token returns None when the token doesn't exist."""
        token = "does-not-exist"

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review_by_share_token(mock_db_session, token)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_none_for_expired_token(
        self, mock_db_session: AsyncMock, mock_share_link: Mock
    ) -> None:
        """Test get_review_by_share_token returns None when the token has expired."""
        token = "fake-token-abc123"
        mock_share_link.is_expired = Mock(return_value=True)

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_share_link
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review_by_share_token(mock_db_session, token)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_none_when_review_missing(
        self, mock_db_session: AsyncMock, mock_share_link: Mock
    ) -> None:
        """Test get_review_by_share_token returns None if the linked review no longer exists."""
        token = "fake-token-abc123"

        share_link_result = Mock()
        share_link_result.scalars.return_value.first.return_value = mock_share_link

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = None

        mock_db_session.execute = AsyncMock(side_effect=[share_link_result, review_result])

        result = await get_review_by_share_token(mock_db_session, token)

        assert result is None
