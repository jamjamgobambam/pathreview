"""Tests for review_service.py"""

import re
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import (
    create_review,
    get_review,
    list_reviews,
)


def make_result(rows=None):
    """Build a mock of the Result returned by awaiting ``AsyncSession.execute()``.

    Only ``execute()`` is awaitable on an ``AsyncSession``; the ``Result`` it
    returns is synchronous, so ``.scalars()``, ``.first()`` and ``.all()`` are
    ordinary calls. Building the result as an ``AsyncMock`` makes
    ``result.scalars()`` return a coroutine, which is what broke these tests.

    Args:
        rows: Rows the statement should yield. Defaults to no rows.

    Returns:
        A ``MagicMock`` whose ``scalars().all()`` returns ``rows`` and whose
        ``scalars().first()`` returns the first row, or ``None`` when empty.
    """
    rows = list(rows or [])
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    result.scalars.return_value.first.return_value = rows[0] if rows else None
    return result


def executed_statement(mock_db_session, index=0):
    """Return the SQLAlchemy statement passed to the ``index``-th execute call."""
    return mock_db_session.execute.call_args_list[index].args[0]


def bound_value(stmt, keyword):
    """Return the bound parameter following ``keyword`` in a compiled statement.

    Used to read the LIMIT/OFFSET values without depending on SQLAlchemy's
    internal parameter naming.
    """
    compiled = stmt.compile()
    match = re.search(rf"{keyword} :(\w+)", str(compiled))
    assert match is not None, f"{keyword} missing from compiled statement:\n{compiled}"
    return compiled.params[match.group(1)]


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
        session.execute = AsyncMock(return_value=make_result())
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
    async def test_create_review_returns_review_with_pending_status(self, mock_db_session):
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as MockReview:
            mock_instance = MockReview.return_value

            result = await create_review(mock_db_session, profile_id, user_id)

            MockReview.assert_called_once()
            assert MockReview.call_args.kwargs["status"] == "pending"
            assert result is mock_instance

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(self, mock_db_session):
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id
        mock_db_session.execute = AsyncMock(return_value=make_result([mock_review]))

        result = await get_review(mock_db_session, review_id, user_id)

        assert result is mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        # No rows come back when the review belongs to a different user.
        mock_db_session.execute = AsyncMock(return_value=make_result([]))

        result = await get_review(mock_db_session, review_id, wrong_user_id)

        assert result is None
        # The wrong user's id must be the one filtered on, or the query would
        # leak another user's review.
        params = executed_statement(mock_db_session).compile().params
        assert wrong_user_id in params.values()

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session):
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # 7 reviews exist in total; page 1 of size 2 returns only the first 2.
        all_reviews = [Mock() for _ in range(7)]
        page_of_reviews = all_reviews[:2]
        mock_db_session.execute = AsyncMock(
            side_effect=[make_result(all_reviews), make_result(page_of_reviews)]
        )

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=2)

        assert reviews == page_of_reviews
        assert total == 7

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(self, mock_db_session):
        """Test list_reviews page 2 returns correct offset."""
        user_id = uuid4()
        page_size = 20

        reviews, total = await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # offset = (page - 1) * page_size
        paginated_stmt = executed_statement(mock_db_session, index=1)
        assert bound_value(paginated_stmt, "OFFSET") == page_size
        assert bound_value(paginated_stmt, "LIMIT") == page_size

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session):
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        result = await list_reviews(mock_db_session, user_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert reviews == []
        assert total == 0

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

        await get_review(mock_db_session, review_id, user_id)

        mock_db_session.execute.assert_called_once()
        sql = str(executed_statement(mock_db_session).compile())
        assert "FROM reviews" in sql
        assert "JOIN profiles ON profiles.id = reviews.profile_id" in sql

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session):
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        await list_reviews(mock_db_session, user_id)

        # Defaults are page=1, page_size=20 -> LIMIT 20 OFFSET 0.
        paginated_stmt = executed_statement(mock_db_session, index=1)
        assert bound_value(paginated_stmt, "LIMIT") == 20
        assert bound_value(paginated_stmt, "OFFSET") == 0

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session):
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        await list_reviews(mock_db_session, user_id, page=1, page_size=custom_page_size)

        paginated_stmt = executed_statement(mock_db_session, index=1)
        assert bound_value(paginated_stmt, "LIMIT") == custom_page_size
        assert bound_value(paginated_stmt, "OFFSET") == 0

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session):
        """Test create_review handles UUID objects correctly."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as MockReview:
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = MockReview.call_args.kwargs
            assert call_kwargs["profile_id"] == profile_id
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session):
        """Test get_review checks Profile.user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        await get_review(mock_db_session, review_id, user_id)

        mock_db_session.execute.assert_called_once()
        stmt = executed_statement(mock_db_session)
        sql = str(stmt.compile())
        # Both the review id and the owning user must constrain the query.
        assert "reviews.id = " in sql
        assert "profiles.user_id = " in sql
        assert set(stmt.compile().params.values()) == {review_id, user_id}

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session):
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        # The count query sees every review; the page query sees one page.
        all_reviews = [Mock() for _ in range(5)]
        mock_db_session.execute = AsyncMock(
            side_effect=[make_result(all_reviews), make_result(all_reviews[:3])]
        )

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=3)

        # total counts all matching reviews, not just the page returned.
        assert total == 5
        assert len(reviews) == 3

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session):
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(3)]
        mock_db_session.execute = AsyncMock(
            side_effect=[make_result(mock_reviews), make_result(mock_reviews)]
        )

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert reviews == mock_reviews
        assert total == 3

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(self, mock_db_session):
        """Test review has None for sections and overall_score initially."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as MockReview:
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = MockReview.call_args.kwargs
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session):
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_db_session.execute = AsyncMock(return_value=make_result([mock_review]))

        result = await get_review(mock_db_session, review_id, user_id)

        # UUIDs pass through to the query unmodified and the row is returned.
        assert result is mock_review
        assert set(executed_statement(mock_db_session).compile().params.values()) == {
            review_id,
            user_id,
        }

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session):
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        await list_reviews(mock_db_session, user_id)

        # list_reviews issues two queries: the count, then the paginated page.
        assert mock_db_session.execute.call_count == 2
        paginated_sql = str(executed_statement(mock_db_session, index=1).compile())
        assert "ORDER BY reviews.created_at DESC" in paginated_sql
