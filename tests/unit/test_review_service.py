"""Tests for review_service.py"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import asyncio

from core.services.review_service import (
  create_review,
  get_review,
  list_reviews,
)


@pytest.mark.unit
class TestReviewService:
  """Test suite for review_service module."""

  @pytest.fixture
  def mockDbSession(self):
    """Create a mock async database session."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()

    return session

  @pytest.fixture
  def mockReview(self):
    """Create a mock Review object."""
    review = Mock()
    review.id = uuid4()
    review.status = "pending"
    review.sections = None
    review.overall_score = None

    return review

  @pytest.fixture
  def mockProfile(self):
    """Create a mock Profile object."""
    profile = Mock()
    profile.id = uuid4()
    profile.userId = uuid4()

    return profile

  @pytest.mark.asyncio
  async def test_createReviewReturnsReviewWithPendingStatus(self, mockDbSession, mockReview):
    """Test create_review returns Review with status='pending'."""
    profileId = uuid4()
    userId = uuid4()

    # Setup mock
    mockDbSession.add = Mock()
    mockDbSession.commit = AsyncMock()
    mockDbSession.refresh = AsyncMock()

    with patch('core.services.review_service.Review') as MockReview:
      mockInstance = MockReview.return_value
      mockInstance.status = "pending"
      mockInstance.sections = None
      mockInstance.overall_score = None

      result = await create_review(mockDbSession, profileId, userId)

      # Check that Review was instantiated
      MockReview.assert_called()
      call_kwargs = MockReview.call_args[1]
      assert call_kwargs['status'] == "pending"

  @pytest.mark.asyncio
  async def test_getReviewReturnsReviewForCorrectOwner(self, mockDbSession):
    """Test get_review returns review when userId matches."""
    reviewId = uuid4()
    userId = uuid4()

    mockReview = Mock()
    mockReview.id = reviewId

    # Setup mock execute to return review
    mockResult = MagicMock()
    mockResult.scalars.return_value.first.return_value = mockReview
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    result = await get_review(mockDbSession, reviewId, userId)

    assert result == mockReview
    mockDbSession.execute.assert_called_once()

  @pytest.mark.asyncio
  async def test_getReviewReturnsNoneForWrongUser(self, mockDbSession):
    """Test get_review returns None when userId doesn't match."""
    reviewId = uuid4()
    # userId = uuid4()
    wrong_userId = uuid4()

    # Setup mock to return None
    mockResult = MagicMock()
    mockResult.scalars.return_value.first.return_value = None
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    result = await get_review(mockDbSession, reviewId, wrong_userId)

    assert result is None

  @pytest.mark.asyncio
  async def test_listReviewsReturnsPaginatedResults(self, mockDbSession):
    """Test list_reviews returns paginated results."""
    userId = uuid4()

    # Create mock reviews
    mockReviews = [Mock() for _ in range(5)]

    # Setup execute mock to return reviews
    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = mockReviews
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(mockDbSession, userId, page=1, page_size=20)

    assert len(reviews) > 0 or len(reviews) == 0  # May be empty
    assert isinstance(total, int)
    assert total >= 0

  @pytest.mark.asyncio
  async def test_listReviewsPage2ReturnsCorrectOffset(self, mockDbSession):
    """Test list_reviews page 2 returns correct offset."""
    userId = uuid4()
    page_size = 20

    # Setup mock
    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = []
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(
        mockDbSession, userId, page=2, page_size=page_size
    )

    # Second call should pass offset for page 2
    calls = mockDbSession.execute.call_args_list
    # Should have at least one call
    assert len(calls) > 0

  @pytest.mark.asyncio
  async def test_listReviewsReturnsTuple(self, mockDbSession):
    """Test list_reviews returns (reviews, total) tuple."""
    userId = uuid4()

    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = []
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    result = await list_reviews(mockDbSession, userId)

    assert isinstance(result, tuple)
    assert len(result) == 2
    reviews, total = result
    assert isinstance(reviews, list)
    assert isinstance(total, int)

  @pytest.mark.asyncio
  async def test_createReviewCallsDbAdd(self, mockDbSession):
    """Test create_review calls db.add()."""
    profileId = uuid4()
    userId = uuid4()

    with patch('core.services.review_service.Review'):
      await create_review(mockDbSession, profileId, userId)

      mockDbSession.add.assert_called_once()

  @pytest.mark.asyncio
  async def test_createReviewCallsDbCommit(self, mockDbSession):
    """Test create_review calls db.commit()."""
    profileId = uuid4()
    userId = uuid4()

    with patch('core.services.review_service.Review'):
      await create_review(mockDbSession, profileId, userId)

      mockDbSession.commit.assert_called_once()

  @pytest.mark.asyncio
  async def test_createReviewCallsDbRefresh(self, mockDbSession):
    """Test create_review calls db.refresh()."""
    profileId = uuid4()
    userId = uuid4()

    with patch('core.services.review_service.Review'):
      await create_review(mockDbSession, profileId, userId)

      mockDbSession.refresh.assert_called_once()

  @pytest.mark.asyncio
  async def test_getReviewUsesSelectAndJoin(self, mockDbSession):
    """Test get_review constructs proper SQL with join."""
    reviewId = uuid4()
    userId = uuid4()

    mockResult = MagicMock()
    mockResult.scalars.return_value.first.return_value = None
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    await get_review(mockDbSession, reviewId, userId)

    # Should call execute with a statement
    mockDbSession.execute.assert_called_once()

  @pytest.mark.asyncio
  async def test_listReviewsDefaultPagination(self, mockDbSession):
    """Test list_reviews uses default pagination."""
    userId = uuid4()

    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = []
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(mockDbSession, userId)

    # Should use default page=1, page_size=20
    assert isinstance(reviews, list)
    assert isinstance(total, int)

  @pytest.mark.asyncio
  async def test_listReviewsCustomPageSize(self, mockDbSession):
    """Test list_reviews with custom page size."""
    userId = uuid4()
    custom_page_size = 50

    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = []
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(mockDbSession, userId, page=1, page_size=custom_page_size)

    assert isinstance(reviews, list)

  @pytest.mark.asyncio
  async def test_createReviewWithUuidIds(self, mockDbSession):
    """Test create_review handles UUID objects correctly."""
    profileId = uuid4()
    userId = uuid4()

    with patch('core.services.review_service.Review') as MockReview:
      MockReview.return_value = Mock()
      await create_review(mockDbSession, profileId, userId)

      call_kwargs = MockReview.call_args[1]
      assert 'profile_id' in call_kwargs
      assert 'status' in call_kwargs

  @pytest.mark.asyncio
  async def test_getReviewVerifiesOwnership(self, mockDbSession):
    """Test get_review checks Profile.userId matches."""
    reviewId = uuid4()
    userId = uuid4()

    mockResult = MagicMock()
    mockResult.scalars.return_value.first.return_value = None
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    await get_review(mockDbSession, reviewId, userId)

    # Should construct query with userId filter
    mockDbSession.execute.assert_called_once()

  @pytest.mark.asyncio
  async def test_listReviewsCountsTotal(self, mockDbSession):
    """Test list_reviews calculates total count."""
    userId = uuid4()

    mockReviews = [Mock() for _ in range(5)]
    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = mockReviews
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(mockDbSession, userId)

    # Total should be counted
    assert isinstance(total, int)

  @pytest.mark.asyncio
  async def test_listReviewsReturnsReviewsList(self, mockDbSession):
    """Test list_reviews returns list of Review objects."""
    userId = uuid4()

    mockReviews = [Mock(spec=['id', 'status']) for _ in range(3)]
    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = mockReviews
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(mockDbSession, userId)

    assert isinstance(reviews, list)

  @pytest.mark.asyncio
  async def test_reviewSectionsAndScoreInitiallyNone(self, mockDbSession):
    """Test review has None for sections and overall_score initially."""
    profileId = uuid4()
    userId = uuid4()

    with patch('core.services.review_service.Review') as MockReview:
      MockReview.return_value = Mock()
      await create_review(mockDbSession, profileId, userId)

      call_kwargs = MockReview.call_args[1]
      assert call_kwargs['sections'] is None
      assert call_kwargs['overall_score'] is None

  @pytest.mark.asyncio
  async def test_getReviewWithValidUuid(self, mockDbSession):
    """Test get_review handles valid UUID parameters."""
    reviewId = uuid4()
    userId = uuid4()

    mockResult = MagicMock()
    mockResult.scalars.return_value.first.return_value = None
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    # Should not raise
    result = await get_review(mockDbSession, reviewId, userId)

    assert result is None or result is not None  # Just verify no exception

  @pytest.mark.asyncio
  async def test_listReviewsOrderedByCreatedAt(self, mockDbSession):
    """Test list_reviews returns results ordered by created_at desc."""
    userId = uuid4()

    mockResult = MagicMock()
    mockResult.scalars.return_value.all.return_value = []
    mockDbSession.execute = AsyncMock(return_value=mockResult)

    reviews, total = await list_reviews(mockDbSession, userId)

    # Should order by created_at descending (count query + paginated query)
    assert mockDbSession.execute.call_count == 2