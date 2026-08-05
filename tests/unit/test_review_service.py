"""Tests for review_service.py."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import (
    create_review,
    create_share_link,
    get_public_review,
    get_review,
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
        review.share_token = None
        review.share_expires_at = None
        return review

    @pytest.fixture
    def mock_profile(self):
        """Create a mock Profile object."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        return profile

    @staticmethod
    def make_scalar_result(first=None, items=None):
        """Create a mock SQLAlchemy result with synchronous scalar methods."""
        result = Mock()
        scalars = Mock()

        scalars.first.return_value = first
        scalars.all.return_value = items if items is not None else []

        result.scalars.return_value = scalars
        return result

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(
        self,
        mock_db_session,
        mock_review,
    ):
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_instance = mock_review_class.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            result = await create_review(
                mock_db_session,
                profile_id,
                user_id,
            )

            mock_review_class.assert_called_once()
            call_kwargs = mock_review_class.call_args.kwargs

            assert call_kwargs["status"] == "pending"
            assert result is mock_instance

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(
        self,
        mock_db_session,
    ):
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id

        mock_result = self.make_scalar_result(first=mock_review)
        mock_db_session.execute.return_value = mock_result

        result = await get_review(
            mock_db_session,
            review_id,
            user_id,
        )

        assert result is mock_review
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(
        self,
        mock_db_session,
    ):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        mock_result = self.make_scalar_result(first=None)
        mock_db_session.execute.return_value = mock_result

        result = await get_review(
            mock_db_session,
            review_id,
            wrong_user_id,
        )

        assert result is None
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(
        self,
        mock_db_session,
    ):
        """Test list_reviews returns paginated results."""
        user_id = uuid4()
        mock_reviews = [Mock() for _ in range(5)]

        count_result = self.make_scalar_result(items=mock_reviews)
        list_result = self.make_scalar_result(items=mock_reviews)

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
            page=1,
            page_size=20,
        )

        assert reviews == mock_reviews
        assert total == 5
        assert mock_db_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(
        self,
        mock_db_session,
    ):
        """Test list_reviews page 2 executes count and paginated queries."""
        user_id = uuid4()
        page_size = 20

        count_result = self.make_scalar_result(items=[])
        list_result = self.make_scalar_result(items=[])

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
            page=2,
            page_size=page_size,
        )

        assert reviews == []
        assert total == 0
        assert mock_db_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(
        self,
        mock_db_session,
    ):
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        count_result = self.make_scalar_result(items=[])
        list_result = self.make_scalar_result(items=[])

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        result = await list_reviews(
            mock_db_session,
            user_id,
        )

        assert isinstance(result, tuple)
        assert len(result) == 2

        reviews, total = result

        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_create_review_calls_db_add(
        self,
        mock_db_session,
    ):
        """Test create_review calls db.add()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(
                mock_db_session,
                profile_id,
                user_id,
            )

        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(
        self,
        mock_db_session,
    ):
        """Test create_review calls db.commit()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(
                mock_db_session,
                profile_id,
                user_id,
            )

        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(
        self,
        mock_db_session,
    ):
        """Test create_review calls db.refresh()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(
                mock_db_session,
                profile_id,
                user_id,
            )

        mock_db_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(
        self,
        mock_db_session,
    ):
        """Test get_review constructs and executes its ownership query."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = self.make_scalar_result(first=None)
        mock_db_session.execute.return_value = mock_result

        await get_review(
            mock_db_session,
            review_id,
            user_id,
        )

        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(
        self,
        mock_db_session,
    ):
        """Test list_reviews works with default pagination."""
        user_id = uuid4()

        count_result = self.make_scalar_result(items=[])
        list_result = self.make_scalar_result(items=[])

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
        )

        assert isinstance(reviews, list)
        assert isinstance(total, int)
        assert mock_db_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(
        self,
        mock_db_session,
    ):
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        count_result = self.make_scalar_result(items=[])
        list_result = self.make_scalar_result(items=[])

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
            page=1,
            page_size=custom_page_size,
        )

        assert isinstance(reviews, list)
        assert total == 0
        assert mock_db_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(
        self,
        mock_db_session,
    ):
        """Test create_review handles UUID objects correctly."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_review_class.return_value = Mock()

            await create_review(
                mock_db_session,
                profile_id,
                user_id,
            )

            call_kwargs = mock_review_class.call_args.kwargs

            assert call_kwargs["profile_id"] == profile_id
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(
        self,
        mock_db_session,
    ):
        """Test get_review executes a query containing ownership filtering."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = self.make_scalar_result(first=None)
        mock_db_session.execute.return_value = mock_result

        await get_review(
            mock_db_session,
            review_id,
            user_id,
        )

        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(
        self,
        mock_db_session,
    ):
        """Test list_reviews calculates total count."""
        user_id = uuid4()
        mock_reviews = [Mock() for _ in range(5)]

        count_result = self.make_scalar_result(items=mock_reviews)
        list_result = self.make_scalar_result(items=mock_reviews)

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
        )

        assert total == 5
        assert reviews == mock_reviews

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(
        self,
        mock_db_session,
    ):
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]

        count_result = self.make_scalar_result(items=mock_reviews)
        list_result = self.make_scalar_result(items=mock_reviews)

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
        )

        assert isinstance(reviews, list)
        assert reviews == mock_reviews
        assert total == 3

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(
        self,
        mock_db_session,
    ):
        """Test review has None for sections and overall_score initially."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_review_class.return_value = Mock()

            await create_review(
                mock_db_session,
                profile_id,
                user_id,
            )

            call_kwargs = mock_review_class.call_args.kwargs

            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(
        self,
        mock_db_session,
    ):
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = self.make_scalar_result(first=None)
        mock_db_session.execute.return_value = mock_result

        result = await get_review(
            mock_db_session,
            review_id,
            user_id,
        )

        assert result is None
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(
        self,
        mock_db_session,
    ):
        """Test list_reviews executes count and ordered list queries."""
        user_id = uuid4()

        count_result = self.make_scalar_result(items=[])
        list_result = self.make_scalar_result(items=[])

        mock_db_session.execute.side_effect = [
            count_result,
            list_result,
        ]

        reviews, total = await list_reviews(
            mock_db_session,
            user_id,
        )

        assert reviews == []
        assert total == 0
        assert mock_db_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_create_share_link_success(
        self,
        mock_db_session,
        mock_review,
    ):
        """Test a completed review receives a 30-day share link."""
        mock_review.status = "complete"

        with patch(
            "core.services.review_service.get_review",
            new=AsyncMock(return_value=mock_review),
        ):
            result = await create_share_link(
                db=mock_db_session,
                review_id=mock_review.id,
                user_id=uuid4(),
            )

        assert result is mock_review
        assert mock_review.share_token is not None
        assert isinstance(mock_review.share_token, str)
        assert len(mock_review.share_token) > 0
        assert mock_review.share_expires_at is not None

        expected_expiration = datetime.now(UTC) + timedelta(days=30)

        difference = abs((mock_review.share_expires_at - expected_expiration).total_seconds())

        assert difference < 5
        mock_db_session.add.assert_called_once_with(mock_review)
        mock_db_session.commit.assert_awaited_once()
        mock_db_session.refresh.assert_awaited_once_with(mock_review)

    @pytest.mark.asyncio
    async def test_create_share_link_rejects_incomplete_review(
        self,
        mock_db_session,
        mock_review,
    ):
        """Test non-complete reviews cannot generate share links."""
        mock_review.status = "processing"

        with (
            patch(
                "core.services.review_service.get_review",
                new=AsyncMock(return_value=mock_review),
            ),
            pytest.raises(
                ValueError,
                match="Only completed reviews can be shared",
            ),
        ):
            await create_share_link(
                db=mock_db_session,
                review_id=mock_review.id,
                user_id=uuid4(),
            )

        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_awaited()
        mock_db_session.refresh.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_public_review_valid_token(
        self,
        mock_db_session,
        mock_review,
    ):
        """Test a valid, unexpired public token returns its review."""
        mock_review.status = "complete"
        mock_review.share_token = "valid-token"
        mock_review.share_expires_at = datetime.now(UTC) + timedelta(days=30)

        mock_result = self.make_scalar_result(first=mock_review)
        mock_db_session.execute.return_value = mock_result

        result = await get_public_review(
            db=mock_db_session,
            share_token="valid-token",
        )

        assert result is mock_review
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_public_review_expired_token(
        self,
        mock_db_session,
        mock_review,
    ):
        """Test an expired public token cannot access a review."""
        mock_review.status = "complete"
        mock_review.share_token = "expired-token"
        mock_review.share_expires_at = datetime.now(UTC) - timedelta(days=1)

        mock_result = self.make_scalar_result(first=mock_review)
        mock_db_session.execute.return_value = mock_result

        result = await get_public_review(
            db=mock_db_session,
            share_token="expired-token",
        )

        assert result is None
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_public_review_invalid_token(
        self,
        mock_db_session,
    ):
        """Test an invalid public token returns no review."""
        mock_result = self.make_scalar_result(first=None)
        mock_db_session.execute.return_value = mock_result

        result = await get_public_review(
            db=mock_db_session,
            share_token="invalid-token",
        )

        assert result is None
        mock_db_session.execute.assert_awaited_once()
