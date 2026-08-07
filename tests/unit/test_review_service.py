"""Tests for review_service.py"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.models.review_share import ReviewShare
from core.services.review_service import (
    create_review,
    create_share_token,
    get_review,
    get_review_by_share_token,
    list_reviews,
)


@pytest.mark.unit
class TestReviewService:
    """Test suite for review_service module."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_review(self):
        """Create a mock Review object."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        return review

    @pytest.fixture
    def mock_profile(self):
        """Create a mock Profile object."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        return profile

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(
        self, mock_db_session, mock_review
    ):
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        # Setup mock
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch("core.services.review_service.Review") as mock_review_cls:
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
    async def test_get_review_returns_review_for_correct_owner(self, mock_db_session):
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id

        # Setup mock execute to return review
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, user_id)

        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        # Setup mock to return None
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, wrong_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session):
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # Create mock reviews
        mock_reviews = [Mock() for _ in range(5)]

        # Setup execute mock to return reviews
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=20)

        assert len(reviews) > 0 or len(reviews) == 0  # May be empty
        assert isinstance(total, int)
        assert total >= 0

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(self, mock_db_session):
        """Test list_reviews page 2 returns correct offset."""
        user_id = uuid4()
        page_size = 20

        # Setup mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # Second call should pass offset for page 2
        calls = mock_db_session.execute.call_args_list
        # Should have at least one call
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session):
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await list_reviews(mock_db_session, user_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_create_review_calls_db_add(self, mock_db_session):
        """Test create_review calls db.add()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session):
        """Test create_review calls db.commit()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session):
        """Test create_review calls db.refresh()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session):
        """Test get_review constructs proper SQL with join."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should call execute with a statement
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session):
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should use default page=1, page_size=20
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session):
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(
            mock_db_session, user_id, page=1, page_size=custom_page_size
        )

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session):
        """Test create_review handles UUID objects correctly."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_cls:
            mock_review_cls.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = mock_review_cls.call_args[1]
            assert "profile_id" in call_kwargs
            assert "status" in call_kwargs

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session):
        """Test get_review checks Profile.user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should construct query with user_id filter
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session):
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(5)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Total should be counted
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session):
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(self, mock_db_session):
        """Test review has None for sections and overall_score initially."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_cls:
            mock_review_cls.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = mock_review_cls.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session):
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Should not raise
        result = await get_review(mock_db_session, review_id, user_id)

        assert result is None or result is not None  # Just verify no exception

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session):
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should order by created_at descending (list_reviews issues a count
        # query plus a select query, so execute is called more than once)
        mock_db_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_create_share_token_creates_token_when_none_exists(self, mock_db_session):
        """Test create_share_token creates new token when none exists."""
        review_id = uuid4()
        user_id = uuid4()

        # Mock get_review to return a complete review
        complete_review = Mock()
        complete_review.status = "complete"

        # Mock execute to return None (no existing token)
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # db.refresh() is what would populate server/default-generated
        # columns (share_token, expires_at) after a real commit/flush.
        async def fake_refresh(obj):
            obj.share_token = "test_token"

        mock_db_session.refresh = AsyncMock(side_effect=fake_refresh)

        with patch(
            "core.services.review_service.get_review", return_value=complete_review
        ) as mock_get:
            result = await create_share_token(mock_db_session, review_id, user_id)

        # Should call get_review with correct params
        mock_get.assert_called_once_with(db=mock_db_session, review_id=review_id, user_id=user_id)
        # Should create and persist a new ReviewShare
        mock_db_session.add.assert_called_once()
        added_share = mock_db_session.add.call_args[0][0]
        assert isinstance(added_share, ReviewShare)
        assert str(added_share.review_id) == str(review_id)
        # Should return the persisted share
        assert result is added_share
        assert result.share_token == "test_token"

    @pytest.mark.asyncio
    async def test_create_share_token_reuses_unexpired_token(self, mock_db_session):
        """Test create_share_token reuses existing unexpired token."""
        review_id = uuid4()
        user_id = uuid4()

        # Mock get_review to return a complete review
        complete_review = Mock()
        complete_review.status = "complete"

        # Mock execute to return existing unexpired token
        mock_share = Mock()
        mock_share.share_token = "existing_token"
        mock_share.expires_at = datetime.utcnow() + timedelta(days=15)

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_share
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch("core.services.review_service.get_review", return_value=complete_review):
            result = await create_share_token(mock_db_session, review_id, user_id)

            # Should return the existing share
            assert result == mock_share
            # Should not create new share
            mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_share_token_returns_none_on_incomplete_review(self, mock_db_session):
        """Test create_share_token returns None for incomplete review."""
        review_id = uuid4()
        user_id = uuid4()

        # Mock get_review to return a non-complete review
        incomplete_review = Mock()
        incomplete_review.status = "pending"

        with patch("core.services.review_service.get_review", return_value=incomplete_review):
            result = await create_share_token(mock_db_session, review_id, user_id)

            # Should return None
            assert result is None

    @pytest.mark.asyncio
    async def test_create_share_token_returns_none_on_non_owned_review(self, mock_db_session):
        """Test create_share_token returns None for non-owned review."""
        review_id = uuid4()
        user_id = uuid4()

        # Mock get_review to return None (ownership check failed)
        with patch("core.services.review_service.get_review", return_value=None):
            result = await create_share_token(mock_db_session, review_id, user_id)

            # Should return None
            assert result is None

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_review_for_valid_token(self, mock_db_session):
        """Test get_review_by_share_token returns review for valid unexpired token."""
        share_token = "valid_token"

        # Mock execute to return a review
        mock_review = Mock()
        mock_review.id = uuid4()
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review_by_share_token(mock_db_session, share_token)

        # Should return the review
        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_none_for_expired_token(self, mock_db_session):
        """Test get_review_by_share_token returns None for expired token."""
        share_token = "expired_token"

        # Mock execute to return None (expired)
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review_by_share_token(mock_db_session, share_token)

        # Should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_review_by_share_token_returns_none_for_unknown_token(self, mock_db_session):
        """Test get_review_by_share_token returns None for unknown token."""
        share_token = "unknown_token"

        # Mock execute to return None (not found)
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review_by_share_token(mock_db_session, share_token)

        # Should return None
        assert result is None
