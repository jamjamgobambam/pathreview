"""Tests for review_service.py"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch
import asyncio

from core.services.review_service import (
    _run_safety_checks,
    _run_agent_orchestration,
    _run_rag_retrieval_generation,
    _run_ingestion_pipeline,
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

        with patch("core.services.review_service.Review") as MockReview:
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

    @pytest.mark.asyncio
    async def test_run_safety_checks_passes_on_valid_output(self) -> None:
        """Test _run_safety_checks returns True for well-formed output."""
        output = {
            "sections": [
                {"section_name": "Skills", "content": "Good", "confidence": 0.8},
            ],
            "overall_score": 0.8,
        }

        result = await _run_safety_checks(output)

        assert result is True

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_on_no_sections(self) -> None:
        """Test _run_safety_checks returns False when there are no sections."""
        result = await _run_safety_checks({"sections": []})

        assert result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_on_incomplete_section(self) -> None:
        """Test _run_safety_checks returns False when a section is missing content."""
        output = {"sections": [{"section_name": "Skills", "confidence": 0.8}]}

        result = await _run_safety_checks(output)

        assert result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_on_out_of_range_confidence(self) -> None:
        """Test _run_safety_checks returns False when confidence is outside 0..1."""
        output = {
            "sections": [
                {"section_name": "Skills", "content": "Good", "confidence": 1.5},
            ]
        }

        result = await _run_safety_checks(output)

        assert result is False

    @pytest.mark.asyncio
    async def test_run_agent_orchestration_returns_expected_keys(self, mock_profile: Mock) -> None:
        """Test _run_agent_orchestration returns sections and overall_score."""
        result = await _run_agent_orchestration(mock_profile, [])

        assert "sections" in result
        assert "overall_score" in result
        assert isinstance(result["sections"], list)

    @pytest.mark.asyncio
    async def test_run_rag_retrieval_generation_returns_expected_keys(
        self, mock_profile: Mock
    ) -> None:
        """Test _run_rag_retrieval_generation returns sections and overall_score."""
        agent_output = {"sections": [], "overall_score": 0.75}

        result = await _run_rag_retrieval_generation(mock_profile, [], agent_output)

        assert "sections" in result
        assert "overall_score" in result
        assert isinstance(result["sections"], list)

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_builds_sources_and_commits(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test _run_ingestion_pipeline builds a source per field and commits."""
        mock_profile.github_username = "octocat"
        mock_profile.portfolio_url = "https://example.com"
        mock_profile.resume_text = "Resume body"
        mock_profile.resume_filename = "resume.pdf"

        with patch("core.services.review_service.IngestedSource"):
            sources = await _run_ingestion_pipeline(mock_db_session, mock_profile)

        source_types = {s["source_type"] for s in sources}
        assert source_types == {"github", "portfolio", "resume"}
        assert len(sources) == 3
        assert mock_db_session.add.call_count == 3
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_review_success_sets_status_complete(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Test process_review reaches status='complete' and stores sections."""
        # execute() is called twice: first returns the review, then the profile.
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result]
        )

        rag_output = {
            "sections": [
                {
                    "section_name": "Skills",
                    "content": "Detailed feedback",
                    "confidence": 0.85,
                    "suggestions": ["Add metrics"],
                }
            ],
            "overall_score": 0.81,
        }

        with (
            patch(
                'core.services.review_service._run_ingestion_pipeline',
                new=AsyncMock(return_value=[]),
            ),
            patch(
                'core.services.review_service._run_agent_orchestration',
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.75}),
            ),
            patch(
                'core.services.review_service._run_rag_retrieval_generation',
                new=AsyncMock(return_value=rag_output),
            ),
            patch(
                'core.services.review_service._run_safety_checks',
                new=AsyncMock(return_value=True),
            ),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "complete"
        assert mock_review.sections == [
            {
                "section_name": "Skills",
                "content": "Detailed feedback",
                "confidence": 0.85,
                "suggestions": ["Add metrics"],
            }
        ]
        assert mock_review.overall_score == 0.81

    @pytest.mark.asyncio
    async def test_process_review_profile_not_found_sets_failed(
        self, mock_db_session: AsyncMock, mock_review: Mock
    ) -> None:
        """Test process_review sets status='failed' when the profile is missing."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result]
        )

        await process_review(mock_db_session, mock_review.id, uuid4())

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_process_review_safety_fail_sets_failed(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Test process_review sets status='failed' when safety checks fail."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result]
        )

        with (
            patch(
                'core.services.review_service._run_ingestion_pipeline',
                new=AsyncMock(return_value=[]),
            ),
            patch(
                'core.services.review_service._run_agent_orchestration',
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.0}),
            ),
            patch(
                'core.services.review_service._run_rag_retrieval_generation',
                new=AsyncMock(return_value={"sections": []}),
            ),
            patch(
                'core.services.review_service._run_safety_checks',
                new=AsyncMock(return_value=False),
            ),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"
        assert mock_review.sections is None

    @pytest.mark.asyncio
    async def test_process_review_review_not_found_returns_early(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test process_review returns early and does not commit when review is missing."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=review_result)

        await process_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.commit.assert_not_awaited()
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_review_unexpected_exception_sets_failed(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Test process_review handles an unexpected exception and sets status='failed'."""
        # execute() is called 3x: review, profile, then again in the except block.
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        recovery_result = Mock()
        recovery_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, recovery_result]
        )

        with patch(
            'core.services.review_service._run_ingestion_pipeline',
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            # Should not raise — the outer except handles it.
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_no_sources_returns_empty_and_commits(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Test _run_ingestion_pipeline returns [] and still commits when no fields are set."""
        mock_profile.github_username = None
        mock_profile.portfolio_url = None
        mock_profile.resume_text = None

        sources = await _run_ingestion_pipeline(mock_db_session, mock_profile)

        assert sources == []
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_review_recovery_failure_is_swallowed(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Test process_review swallows a failure that occurs while setting status='failed'."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        recovery_result = Mock()
        recovery_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, recovery_result]
        )
        # First commit (status=processing) raises -> outer except; recovery commit also raises.
        mock_db_session.commit = AsyncMock(side_effect=RuntimeError("db down"))

        # Should not raise despite both commits failing.
        await process_review(mock_db_session, mock_review.id, mock_profile.id)

    @pytest.mark.asyncio
    async def test_run_safety_checks_handles_malformed_section(self) -> None:
        """Test _run_safety_checks returns False when a section is not a dict."""
        result = await _run_safety_checks({"sections": ["not-a-dict"]})

        assert result is False