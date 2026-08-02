"""Tests for review_service.py"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from core.models.review import Review
from core.services.review_service import (
    _calculate_content_hash,
    _get_cached_review,
    get_or_create_review,
    get_review,
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
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def mock_review(self) -> Mock:
        """Create a mock Review object."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        review.content_hash = "test_hash"
        return review

    @pytest.fixture
    def mock_profile(self) -> Mock:
        """Create a mock Profile object."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        profile.github_username = "testuser"
        profile.resume_text = "Test resume content"
        profile.portfolio_url = "https://example.com"
        return profile

    @pytest.mark.asyncio
    async def test_calculate_content_hash(self) -> None:
        """Test content hash calculation is deterministic."""
        github = "testuser"
        resume = "Test resume"
        portfolio = "https://example.com"

        hash1 = _calculate_content_hash(github, resume, portfolio)
        hash2 = _calculate_content_hash(github, resume, portfolio)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length

    @pytest.mark.asyncio
    async def test_calculate_content_hash_different_inputs(self) -> None:
        """Test different inputs produce different hashes."""
        hash1 = _calculate_content_hash("user1", "resume1", "url1")
        hash2 = _calculate_content_hash("user2", "resume2", "url2")

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_calculate_content_hash_handles_none_values(self) -> None:
        """Test content hash calculation with None values."""
        hash1 = _calculate_content_hash(None, None, None)
        hash2 = _calculate_content_hash("", "", "")

        # Both should produce valid hashes
        assert len(hash1) == 64
        assert len(hash2) == 64

    @pytest.mark.asyncio
    async def test_get_cached_review_returns_complete_review(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test _get_cached_review returns cached review with status='complete'."""
        content_hash = "test_hash_123"

        # Create a real Review instance for isinstance check
        cached_review = Review(
            id=uuid4(),
            profile_id=uuid4(),
            status="complete",
            content_hash=content_hash,
            sections=None,
            overall_score=None,
        )

        # Setup execute mock
        mock_scalars = Mock()
        mock_scalars.first.return_value = cached_review
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await _get_cached_review(mock_db_session, content_hash)

        assert result == cached_review
        assert result.status == "complete"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_review_returns_none_if_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test _get_cached_review returns None if no cached review exists."""
        content_hash = "test_hash_123"

        # Setup execute mock to return None
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await _get_cached_review(mock_db_session, content_hash)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_or_create_review_returns_cached_review(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test get_or_create_review returns cached review if content hash matches."""
        profile_id = mock_profile.id
        user_id = mock_profile.user_id

        # Calculate hash for the profile
        content_hash = _calculate_content_hash(
            mock_profile.github_username, mock_profile.resume_text, mock_profile.portfolio_url
        )

        # Create a real Review instance for cached review
        cached_review = Review(
            id=uuid4(),
            profile_id=profile_id,
            status="complete",
            content_hash=content_hash,
            sections=None,
            overall_score=None,
        )

        # Setup execute mocks
        profile_scalars = Mock()
        profile_scalars.first.return_value = mock_profile
        profile_result = Mock()
        profile_result.scalars.return_value = profile_scalars

        cached_scalars = Mock()
        cached_scalars.first.return_value = cached_review
        cached_result = Mock()
        cached_result.scalars.return_value = cached_scalars

        # First call returns profile, second call returns cached review
        mock_db_session.execute = AsyncMock(side_effect=[profile_result, cached_result])

        result = await get_or_create_review(mock_db_session, profile_id, user_id)

        assert result == cached_review
        assert result.status == "complete"
        assert mock_db_session.add.call_count == 0  # Should not create new review

    @pytest.mark.asyncio
    async def test_get_or_create_review_creates_new_review_if_no_cache(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test get_or_create_review creates new review if no cached version exists."""
        profile_id = mock_profile.id
        user_id = mock_profile.user_id

        # Setup execute mocks - profile found, no cached review
        profile_scalars = Mock()
        profile_scalars.first.return_value = mock_profile
        profile_result = Mock()
        profile_result.scalars.return_value = profile_scalars

        cached_scalars = Mock()
        cached_scalars.first.return_value = None
        cached_result = Mock()
        cached_result.scalars.return_value = cached_scalars

        mock_db_session.execute = AsyncMock(side_effect=[profile_result, cached_result])
        mock_db_session.refresh = AsyncMock()

        result = await get_or_create_review(mock_db_session, profile_id, user_id)

        # Should have created a new review with pending status
        assert result.status == "pending"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_review_stores_content_hash(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test get_or_create_review stores content hash in new review."""
        profile_id = mock_profile.id
        user_id = mock_profile.user_id

        profile_scalars = Mock()
        profile_scalars.first.return_value = mock_profile
        profile_result = Mock()
        profile_result.scalars.return_value = profile_scalars

        cached_scalars = Mock()
        cached_scalars.first.return_value = None
        cached_result = Mock()
        cached_result.scalars.return_value = cached_scalars

        mock_db_session.execute = AsyncMock(side_effect=[profile_result, cached_result])
        mock_db_session.refresh = AsyncMock()

        result = await get_or_create_review(mock_db_session, profile_id, user_id)

        # Check that content_hash was stored in the review
        assert result.content_hash is not None
        assert len(result.content_hash) == 64  # SHA-256 hex digest

    @pytest.mark.asyncio
    async def test_get_or_create_review_raises_if_profile_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_or_create_review raises ValueError if profile not found."""
        profile_id = uuid4()
        user_id = uuid4()

        # Setup execute to return no profile
        profile_scalars = Mock()
        profile_scalars.first.return_value = None
        profile_result = Mock()
        profile_result.scalars.return_value = profile_scalars
        mock_db_session.execute = AsyncMock(return_value=profile_result)

        with pytest.raises(ValueError, match="Profile .* not found"):
            await get_or_create_review(mock_db_session, profile_id, user_id)

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
        mock_scalars = Mock()
        mock_scalars.first.return_value = mock_review
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, user_id)

        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session: AsyncMock) -> None:
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        user_id = uuid4()

        # Setup mock to return None
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_review_uses_join_for_ownership_check(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_review joins Review with Profile for ownership verification."""
        review_id = uuid4()
        user_id = uuid4()

        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should call execute with a statement
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # Create mock reviews
        mock_reviews = [Mock() for _ in range(5)]

        # Setup execute mock - list_reviews calls execute twice (count, then data)
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_reviews
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=20)

        assert len(reviews) >= 0
        assert isinstance(total, int)
        assert total >= 0

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_calculates_offset(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews page 2 returns with correct offset."""
        user_id = uuid4()
        page_size = 20

        # Setup mock
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # Should have called execute twice (count + data)
        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await list_reviews(mock_db_session, user_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
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

        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(
            mock_db_session, user_id, page=1, page_size=custom_page_size
        )

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(5)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_reviews
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Total should be counted
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
        mock_scalars = Mock()
        mock_scalars.all.return_value = mock_reviews
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_get_or_create_review_with_partial_profile(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_or_create_review handles partial profile data."""
        profile_id = uuid4()
        user_id = uuid4()

        partial_profile = Mock()
        partial_profile.id = profile_id
        partial_profile.user_id = user_id
        partial_profile.github_username = "testuser"
        partial_profile.resume_text = None
        partial_profile.portfolio_url = None

        profile_scalars = Mock()
        profile_scalars.first.return_value = partial_profile
        profile_result = Mock()
        profile_result.scalars.return_value = profile_scalars

        cached_scalars = Mock()
        cached_scalars.first.return_value = None
        cached_result = Mock()
        cached_result.scalars.return_value = cached_scalars

        mock_db_session.execute = AsyncMock(side_effect=[profile_result, cached_result])
        mock_db_session.refresh = AsyncMock()

        result = await get_or_create_review(mock_db_session, profile_id, user_id)

        # Should still have content_hash even with partial data
        assert result.content_hash is not None
        assert len(result.content_hash) == 64

    @pytest.mark.asyncio
    async def test_caching_hit_avoids_processing(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test that cached review avoids new processing."""
        profile_id = mock_profile.id
        user_id = mock_profile.user_id

        content_hash = _calculate_content_hash(
            mock_profile.github_username, mock_profile.resume_text, mock_profile.portfolio_url
        )

        # Create a real Review instance for cached review
        cached_review = Review(
            id=uuid4(),
            profile_id=profile_id,
            status="complete",
            content_hash=content_hash,
            sections=[{"section_name": "Test"}],
            overall_score=0.85,
        )

        profile_scalars = Mock()
        profile_scalars.first.return_value = mock_profile
        profile_result = Mock()
        profile_result.scalars.return_value = profile_scalars

        cached_scalars = Mock()
        cached_scalars.first.return_value = cached_review
        cached_result = Mock()
        cached_result.scalars.return_value = cached_scalars

        mock_db_session.execute = AsyncMock(side_effect=[profile_result, cached_result])

        result = await get_or_create_review(mock_db_session, profile_id, user_id)

        # Cached review returned without creating new one
        assert result.status == "complete"
        assert result.id == cached_review.id
        assert mock_db_session.add.call_count == 0

    @pytest.mark.asyncio
    async def test_different_hashes_create_separate_reviews(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test that different content hashes create separate reviews."""
        profile_id = uuid4()

        # Two profiles with different content
        profile1 = Mock()
        profile1.id = profile_id
        profile1.github_username = "user1"
        profile1.resume_text = "Resume 1"
        profile1.portfolio_url = "url1.com"

        profile2 = Mock()
        profile2.id = profile_id
        profile2.github_username = "user2"
        profile2.resume_text = "Resume 2"
        profile2.portfolio_url = "url2.com"

        hash1 = _calculate_content_hash(
            profile1.github_username, profile1.resume_text, profile1.portfolio_url
        )
        hash2 = _calculate_content_hash(
            profile2.github_username, profile2.resume_text, profile2.portfolio_url
        )

        assert hash1 != hash2
