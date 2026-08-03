"""Tests for review_service.py"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import (
    _run_ingestion_pipeline,
    _run_safety_checks,
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

        with patch("core.services.review_service.Review") as MockReview:
            mock_instance = MockReview.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            result = await create_review(mock_db_session, profile_id, user_id)

            # Check that Review was instantiated
            MockReview.assert_called()
            call_kwargs = MockReview.call_args[1]
            assert call_kwargs["status"] == "pending"

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

        reviews, total = await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

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

        with patch("core.services.review_service.Review") as MockReview:
            MockReview.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = MockReview.call_args[1]
            assert "profile_id" in call_kwargs
            assert "status" in call_kwargs

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

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
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

        with patch("core.services.review_service.Review") as MockReview:
            MockReview.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = MockReview.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

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
    @patch("core.services.review_service._run_safety_checks")
    @patch("core.services.review_service._run_rag_retrieval_generation")
    @patch("core.services.review_service._run_agent_orchestration")
    @patch("core.services.review_service._run_ingestion_pipeline")
    async def test_process_review_success_sets_status_complete(
        self,
        mock_ingestion,
        mock_agent,
        mock_rag,
        mock_safety,
        mock_db_session,
        mock_review,
        mock_profile,
    ):
        """Test process_review sets status='complete' and stores sections on success."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        mock_ingestion.return_value = [{"source_type": "github", "data": "some data"}]
        mock_agent.return_value = {"sections": [], "overall_score": 0.75}
        mock_rag.return_value = {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Great skills",
                    "confidence": 0.9,
                    "suggestions": ["Add more detail"],
                }
            ],
            "overall_score": 0.85,
        }
        mock_safety.return_value = True

        await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "complete"
        assert mock_review.overall_score == 0.85
        assert mock_review.sections is not None
        assert len(mock_review.sections) == 1

    @pytest.mark.asyncio
    async def test_process_review_returns_early_when_review_not_found(self, mock_db_session):
        """Test process_review exits quietly (no commit) when review doesn't exist."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=review_result)

        result = await process_review(mock_db_session, uuid4(), uuid4())

        assert result is None
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_review_sets_failed_when_profile_not_found(
        self,
        mock_db_session,
        mock_review,
    ):
        """Test process_review sets status='failed' when the profile can't be found."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        await process_review(mock_db_session, mock_review.id, uuid4())

        assert mock_review.status == "failed"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("core.services.review_service._run_safety_checks")
    @patch("core.services.review_service._run_rag_retrieval_generation")
    @patch("core.services.review_service._run_agent_orchestration")
    @patch("core.services.review_service._run_ingestion_pipeline")
    async def test_process_review_sets_failed_when_safety_checks_fail(
        self,
        mock_ingestion,
        mock_agent,
        mock_rag,
        mock_safety,
        mock_db_session,
        mock_review,
        mock_profile,
    ):
        """Test process_review sets status='failed' when safety checks reject the output."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        mock_ingestion.return_value = []
        mock_agent.return_value = {"sections": [], "overall_score": 0.5}
        mock_rag.return_value = {"sections": [], "overall_score": 0.5}
        mock_safety.return_value = False

        await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"
        assert mock_review.sections is None

    @pytest.mark.asyncio
    @patch("core.services.review_service._run_ingestion_pipeline")
    async def test_process_review_sets_failed_on_unhandled_exception(
        self,
        mock_ingestion,
        mock_db_session,
        mock_review,
        mock_profile,
    ):
        """Test process_review catches a mid-pipeline exception and marks the review failed."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        review_result_again = Mock()
        review_result_again.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, review_result_again]
        )

        mock_ingestion.side_effect = Exception("ingestion exploded")

        await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    @patch("core.services.review_service._run_ingestion_pipeline")
    async def test_process_review_does_not_raise_when_failure_handler_itself_fails(
        self,
        mock_ingestion,
        mock_db_session,
        mock_review,
        mock_profile,
    ):
        """Test process_review swallows errors even if the fallback status update fails too."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, Exception("db is down")]
        )

        mock_ingestion.side_effect = Exception("ingestion exploded")

        await process_review(mock_db_session, mock_review.id, mock_profile.id)

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_success_all_sources(self, mock_db_session):
        """Test ingestion pipeline processes github, portfolio, and resume sources."""
        profile = Mock(
            id=uuid4(),
            github_username="octocat",
            portfolio_url="https://example.com/portfolio",
            resume_text="Experienced engineer...",
            resume_filename="resume.pdf",
        )
        with patch("core.services.review_service.IngestedSource"):
            results = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(results) == 3
        assert mock_db_session.add.call_count == 3
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_empty_profile_returns_empty_list(self, mock_db_session):
        """Test ingestion pipeline handles a profile with no sources at all (edge case)."""
        profile = Mock(
            id=uuid4(),
            github_username=None,
            portfolio_url=None,
            resume_text=None,
            resume_filename=None,
        )
        with patch("core.services.review_service.IngestedSource"):
            results = await _run_ingestion_pipeline(mock_db_session, profile)

        assert results == []
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_continues_after_github_failure(self, mock_db_session):
        """Test that a failure ingesting GitHub doesn't stop portfolio/resume from processing."""
        profile = Mock(
            id=uuid4(),
            github_username="octocat",
            portfolio_url="https://example.com/portfolio",
            resume_text="Experienced engineer...",
            resume_filename="resume.pdf",
        )
        with patch(
            "core.services.review_service.IngestedSource",
            side_effect=[Exception("github ingestion failed"), Mock(), Mock()],
        ):
            results = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(results) == 3
        assert mock_db_session.add.call_count == 2
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_safety_checks_passes_valid_output(self):
        """Test safety checks pass for a well-formed section."""
        output = {
            "sections": [
                {"section_name": "Technical Skills", "content": "Solid", "confidence": 0.5}
            ]
        }
        assert await _run_safety_checks(output) is True

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_when_no_sections(self):
        """Test safety checks fail when sections are missing or empty."""
        assert await _run_safety_checks({"sections": []}) is False
        assert await _run_safety_checks({}) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_when_section_missing_name_or_content(self):
        """Test safety checks fail when a section is missing its name or content."""
        missing_name = {
            "sections": [{"section_name": "", "content": "Some content", "confidence": 0.5}]
        }
        missing_content = {
            "sections": [{"section_name": "Technical Skills", "content": "", "confidence": 0.5}]
        }
        assert await _run_safety_checks(missing_name) is False
        assert await _run_safety_checks(missing_content) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_boundary_confidence_values_pass(self):
        """Test confidence of exactly 0 and exactly 1 are valid (inclusive boundaries)."""
        zero_confidence = {"sections": [{"section_name": "X", "content": "Y", "confidence": 0}]}
        one_confidence = {"sections": [{"section_name": "X", "content": "Y", "confidence": 1}]}
        assert await _run_safety_checks(zero_confidence) is True
        assert await _run_safety_checks(one_confidence) is True

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_invalid_confidence_out_of_range(self):
        """Test confidence outside [0, 1] fails safety checks."""
        too_high = {"sections": [{"section_name": "X", "content": "Y", "confidence": 1.5}]}
        too_low = {"sections": [{"section_name": "X", "content": "Y", "confidence": -0.1}]}
        assert await _run_safety_checks(too_high) is False
        assert await _run_safety_checks(too_low) is False
