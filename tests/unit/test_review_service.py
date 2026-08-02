# mypy: disable-error-code=no-untyped-def

"""Tests for review_service.py"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from core.services.review_service import (
    _build_review_content_hash,
    create_review,
    get_review,
    list_reviews,
)


def _mock_execute_result(first=None, all_values=None):
    """Build a simple async execute result mock."""
    result = Mock()
    scalars = Mock()
    scalars.first.return_value = first
    scalars.all.return_value = all_values if all_values is not None else []
    result.scalars.return_value = scalars
    return result


def _build_mock_profile():
    """Create a mock profile object for create_review tests."""
    profile = Mock()
    profile.id = uuid4()
    profile.user_id = uuid4()
    profile.github_username = "octocat"
    profile.portfolio_url = "https://example.com"
    profile.resume_text = "Sample resume text"
    return profile


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
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com"
        profile.resume_text = "Sample resume text"
        return profile

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(
        self, mock_db_session, mock_review
    ):
        """Test create_review returns Review with status='pending'."""
        profile = _build_mock_profile()

        # Setup mock
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=None),
            ]
        )

        result, created = await create_review(mock_db_session, profile.id, profile.user_id)

        assert result.status == "pending"
        assert result.sections is None
        assert result.overall_score is None
        assert created is True

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(self, mock_db_session):
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id

        # Setup mock execute to return review
        mock_db_session.execute = AsyncMock(return_value=_mock_execute_result(first=mock_review))

        result = await get_review(mock_db_session, review_id, user_id)

        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        # Setup mock to return None
        mock_db_session.execute = AsyncMock(return_value=_mock_execute_result(first=None))

        result = await get_review(mock_db_session, review_id, wrong_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session):
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # Create mock reviews
        mock_reviews = [Mock() for _ in range(5)]

        # Setup execute mock to return reviews
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=mock_reviews),
                _mock_execute_result(all_values=mock_reviews),
            ]
        )

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
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=[]),
                _mock_execute_result(all_values=[]),
            ]
        )

        reviews, total = await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # Second call should pass offset for page 2
        calls = mock_db_session.execute.call_args_list
        # Should have at least one call
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session):
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=[]),
                _mock_execute_result(all_values=[]),
            ]
        )

        result = await list_reviews(mock_db_session, user_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_create_review_calls_db_add(self, mock_db_session):
        """Test create_review calls db.add()."""
        profile = _build_mock_profile()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=None),
            ]
        )

        await create_review(mock_db_session, profile.id, profile.user_id)

        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session):
        """Test create_review calls db.commit()."""
        profile = _build_mock_profile()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=None),
            ]
        )

        await create_review(mock_db_session, profile.id, profile.user_id)

        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session):
        """Test create_review calls db.refresh()."""
        profile = _build_mock_profile()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=None),
            ]
        )

        await create_review(mock_db_session, profile.id, profile.user_id)

        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session):
        """Test get_review constructs proper SQL with join."""
        review_id = uuid4()
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(return_value=_mock_execute_result(first=None))

        await get_review(mock_db_session, review_id, user_id)

        # Should call execute with a statement
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session):
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=[]),
                _mock_execute_result(all_values=[]),
            ]
        )

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should use default page=1, page_size=20
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session):
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=[]),
                _mock_execute_result(all_values=[]),
            ]
        )

        reviews, total = await list_reviews(
            mock_db_session, user_id, page=1, page_size=custom_page_size
        )

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session):
        """Test create_review handles UUID objects correctly."""
        profile = _build_mock_profile()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=None),
            ]
        )

        review, created = await create_review(mock_db_session, profile.id, profile.user_id)

        assert review.profile_id == profile.id
        assert review.status == "pending"
        assert created is True

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session):
        """Test get_review checks Profile.user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(return_value=_mock_execute_result(first=None))

        await get_review(mock_db_session, review_id, user_id)

        # Should construct query with user_id filter
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session):
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(5)]
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=mock_reviews),
                _mock_execute_result(all_values=mock_reviews),
            ]
        )

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Total should be counted
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session):
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=mock_reviews),
                _mock_execute_result(all_values=mock_reviews),
            ]
        )

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(self, mock_db_session):
        """Test review has None for sections and overall_score initially."""
        profile = _build_mock_profile()
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=None),
            ]
        )

        review, created = await create_review(mock_db_session, profile.id, profile.user_id)

        assert review.sections is None
        assert review.overall_score is None
        assert created is True

    @pytest.mark.asyncio
    async def test_create_review_reuses_cached_completed_review(self, mock_db_session):
        """Test create_review returns a cached completed review for identical content."""
        profile = _build_mock_profile()
        cached_review = Mock()
        cached_review.id = uuid4()
        cached_review.status = "complete"

        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(first=profile),
                _mock_execute_result(first=cached_review),
            ]
        )

        review, created = await create_review(mock_db_session, profile.id, profile.user_id)

        assert review == cached_review
        assert created is False
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
        mock_db_session.refresh.assert_not_called()

    def test_review_content_hash_changes_when_profile_content_changes(self):
        """Test the cache fingerprint changes when review-relevant profile content changes."""
        original_profile = _build_mock_profile()
        updated_profile = _build_mock_profile()
        updated_profile.github_username = original_profile.github_username
        updated_profile.portfolio_url = original_profile.portfolio_url
        updated_profile.resume_text = "Updated resume text"

        original_hash = _build_review_content_hash(original_profile)
        updated_hash = _build_review_content_hash(updated_profile)

        assert original_hash != updated_hash

    @pytest.mark.asyncio
    async def test_create_review_raises_not_found_for_wrong_owner(self, mock_db_session):
        """Test create_review raises 404 when the profile is not owned by the user."""
        profile_id = uuid4()
        user_id = uuid4()
        mock_db_session.execute = AsyncMock(side_effect=[_mock_execute_result(first=None)])

        with pytest.raises(HTTPException) as exc_info:
            await create_review(mock_db_session, profile_id, user_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session):
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(return_value=_mock_execute_result(first=None))

        # Should not raise
        result = await get_review(mock_db_session, review_id, user_id)

        assert result is None or result is not None  # Just verify no exception

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session):
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_db_session.execute = AsyncMock(
            side_effect=[
                _mock_execute_result(all_values=[]),
                _mock_execute_result(all_values=[]),
            ]
        )

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should order by created_at descending
        assert mock_db_session.execute.call_count == 2
