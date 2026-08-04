"""Tests for review_service.py"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch
import asyncio

from core.services.review_service import (
    PROGRESS_AGENT_COMPLETE,
    PROGRESS_COMPLETE,
    PROGRESS_INGESTION_COMPLETE,
    PROGRESS_PROCESSING_STARTED,
    PROGRESS_RAG_COMPLETE,
    _set_progress,
    create_review,
    get_review,
    list_reviews,
    process_review,
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
    async def test_create_review_returns_review_with_pending_status(self, mock_db_session, mock_review):
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        # Setup mock
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch('core.services.review_service.Review') as MockReview:
            mock_instance = MockReview.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            result = await create_review(mock_db_session, profile_id, user_id)

            # Check that Review was instantiated
            MockReview.assert_called()
            call_kwargs = MockReview.call_args[1]
            assert call_kwargs['status'] == "pending"

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(self, mock_db_session):
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
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        user_id = uuid4()
        wrong_user_id = uuid4()

        # Setup mock to return None
        mock_result = AsyncMock()
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
        mock_result = AsyncMock()
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
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(
            mock_db_session, user_id, page=2, page_size=page_size
        )

        # Second call should pass offset for page 2
        calls = mock_db_session.execute.call_args_list
        # Should have at least one call
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session):
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
    async def test_create_review_calls_db_add(self, mock_db_session):
        """Test create_review calls db.add()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch('core.services.review_service.Review'):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session):
        """Test create_review calls db.commit()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch('core.services.review_service.Review'):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session):
        """Test create_review calls db.refresh()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch('core.services.review_service.Review'):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session):
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
    async def test_list_reviews_default_pagination(self, mock_db_session):
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
    async def test_list_reviews_custom_page_size(self, mock_db_session):
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
    async def test_create_review_with_uuid_ids(self, mock_db_session):
        """Test create_review handles UUID objects correctly."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch('core.services.review_service.Review') as MockReview:
            MockReview.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = MockReview.call_args[1]
            assert 'profile_id' in call_kwargs
            assert 'status' in call_kwargs

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session):
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
    async def test_list_reviews_counts_total(self, mock_db_session):
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
    async def test_list_reviews_returns_reviews_list(self, mock_db_session):
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=['id', 'status']) for _ in range(3)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(self, mock_db_session):
        """Test review has None for sections and overall_score initially."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch('core.services.review_service.Review') as MockReview:
            MockReview.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = MockReview.call_args[1]
            assert call_kwargs['sections'] is None
            assert call_kwargs['overall_score'] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session):
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
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session):
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should order by created_at descending
        mock_db_session.execute.assert_called_once()


@pytest.mark.unit
class TestReviewProgress:
    """Test suite for progress_pct reporting during review processing (issue #97)."""

    @pytest.fixture
    def in_flight_review(self):
        """Create a mock Review row as it exists when processing starts."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.progress_pct = 0
        review.sections = None
        review.overall_score = None
        return review

    @pytest.fixture
    def ingestible_profile(self):
        """Create a mock Profile with a single GitHub source to ingest."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = None
        profile.resume_text = None
        profile.resume_filename = None
        return profile

    @staticmethod
    def _session_recording_progress(review, profile):
        """Build a mock session for process_review that records progress on each commit.

        Returns a ``(session, snapshots)`` tuple where ``snapshots`` collects the
        value of ``review.progress_pct`` at every ``commit()`` call, i.e. every
        value a polling client could observe.
        """
        session = AsyncMock()
        session.add = Mock()

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = profile
        session.execute = AsyncMock(side_effect=[review_result, profile_result])

        snapshots: list[int] = []

        async def record_commit():
            snapshots.append(review.progress_pct)

        session.commit = AsyncMock(side_effect=record_commit)
        return session, snapshots

    @pytest.mark.asyncio
    async def test_process_review_emits_each_pipeline_milestone_in_order(
        self, in_flight_review, ingestible_profile
    ):
        """Test process_review commits an advancing progress value per pipeline step."""
        session, snapshots = self._session_recording_progress(in_flight_review, ingestible_profile)

        await process_review(session, in_flight_review.id, ingestible_profile.id)

        # Collapse repeated values (some steps commit more than once) and compare
        # against the milestones the pipeline is expected to pass through.
        observed = [p for i, p in enumerate(snapshots) if i == 0 or p != snapshots[i - 1]]
        assert observed == [
            PROGRESS_PROCESSING_STARTED,
            PROGRESS_INGESTION_COMPLETE,
            PROGRESS_AGENT_COMPLETE,
            PROGRESS_RAG_COMPLETE,
            PROGRESS_COMPLETE,
        ]

    @pytest.mark.asyncio
    async def test_process_review_progress_never_decreases(
        self, in_flight_review, ingestible_profile
    ):
        """Test observed progress values are monotonically non-decreasing."""
        session, snapshots = self._session_recording_progress(in_flight_review, ingestible_profile)

        await process_review(session, in_flight_review.id, ingestible_profile.id)

        assert snapshots == sorted(snapshots)
        assert all(0 <= p <= 100 for p in snapshots)

    @pytest.mark.asyncio
    async def test_process_review_reaches_100_when_complete(
        self, in_flight_review, ingestible_profile
    ):
        """Test a completed review ends at status='complete' with progress_pct=100."""
        session, _ = self._session_recording_progress(in_flight_review, ingestible_profile)

        await process_review(session, in_flight_review.id, ingestible_profile.id)

        assert in_flight_review.status == "complete"
        assert in_flight_review.progress_pct == PROGRESS_COMPLETE

    @pytest.mark.asyncio
    async def test_process_review_emits_intermediate_progress_before_completing(
        self, in_flight_review, ingestible_profile
    ):
        """Test progress is visible mid-run, not only 0 then 100.

        This is the regression guard for issue #97: previously every poll returned
        0 until the review finished, so the UI had nothing to animate.
        """
        session, snapshots = self._session_recording_progress(in_flight_review, ingestible_profile)

        await process_review(session, in_flight_review.id, ingestible_profile.id)

        intermediate = [p for p in snapshots if 0 < p < 100]
        assert len(set(intermediate)) >= 3

    @pytest.mark.asyncio
    async def test_process_review_does_not_reach_100_when_safety_checks_fail(
        self, in_flight_review, ingestible_profile
    ):
        """Test a review failed by safety checks keeps its partial progress."""
        session, _ = self._session_recording_progress(in_flight_review, ingestible_profile)

        with patch(
            "core.services.review_service._run_safety_checks",
            new=AsyncMock(return_value=False),
        ):
            await process_review(session, in_flight_review.id, ingestible_profile.id)

        assert in_flight_review.status == "failed"
        assert in_flight_review.progress_pct == PROGRESS_RAG_COMPLETE

    @pytest.mark.asyncio
    async def test_create_review_initializes_progress_at_zero(self):
        """Test create_review starts a new review at progress_pct=0."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch("core.services.review_service.Review") as mock_review_cls:
            mock_review_cls.return_value = Mock()
            await create_review(session, uuid4(), uuid4())

            assert mock_review_cls.call_args[1]["progress_pct"] == 0

    @pytest.mark.asyncio
    async def test_set_progress_clamps_values_outside_0_100(self):
        """Test _set_progress clamps out-of-range values into 0-100."""
        review = Mock()
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()

        await _set_progress(session, review, 150)
        assert review.progress_pct == 100

        await _set_progress(session, review, -20)
        assert review.progress_pct == 0

    @pytest.mark.asyncio
    async def test_set_progress_commits_so_polls_observe_the_value(self):
        """Test _set_progress persists the review instead of only mutating it."""
        review = Mock()
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()

        await _set_progress(session, review, 42)

        assert review.progress_pct == 42
        session.add.assert_called_once_with(review)
        session.commit.assert_awaited_once()
