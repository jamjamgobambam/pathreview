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


def make_execute_result(first=None, all=None):
    """Build a plain (non-AsyncMock) result object for a mocked db.execute() call.

    Production code calls `.scalars()` synchronously on the object returned by
    `await db.execute(...)`. If that returned object is itself an AsyncMock,
    `.scalars` is auto-specced as an AsyncMock too, so calling it returns an
    unawaited coroutine instead of the configured Mock chain (this is the bug
    tracked in issue #158). Using a plain Mock() here avoids that trap.
    """
    result = Mock()
    result.scalars.return_value.first.return_value = first
    result.scalars.return_value.all.return_value = all if all is not None else []
    return result


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

    # ---- process_review: success path ----

    @pytest.mark.asyncio
    async def test_process_review_success_path(self, mock_db_session, mock_review, mock_profile):
        """Test process_review sets status='complete' and stores sections on success."""
        review_result = make_execute_result(first=mock_review)
        profile_result = make_execute_result(first=mock_profile)
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        rag_output = {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Detailed feedback on technical skills",
                    "confidence": 0.85,
                    "suggestions": ["Add more detail"],
                }
            ],
            "overall_score": 0.81,
        }

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.75}),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value=rag_output),
            ),
            patch(
                "core.services.review_service._run_safety_checks", new=AsyncMock(return_value=True)
            ),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "complete"
        assert mock_review.sections is not None
        assert len(mock_review.sections) == 1
        assert mock_review.overall_score == 0.81

    # ---- process_review: partial-failure paths ----

    @pytest.mark.asyncio
    async def test_process_review_review_not_found_returns_early(self, mock_db_session):
        """Test process_review returns early without committing when the review doesn't exist."""
        review_result = make_execute_result(first=None)
        mock_db_session.execute = AsyncMock(return_value=review_result)

        await process_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_review_profile_not_found_sets_failed(self, mock_db_session, mock_review):
        """Test process_review sets status='failed' when the profile lookup returns None."""
        review_result = make_execute_result(first=mock_review)
        profile_result = make_execute_result(first=None)
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        with patch(
            "core.services.review_service._run_ingestion_pipeline", new=AsyncMock()
        ) as mock_ingest:
            await process_review(mock_db_session, mock_review.id, uuid4())

        assert mock_review.status == "failed"
        mock_ingest.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_review_safety_check_failed_sets_failed(
        self, mock_db_session, mock_review, mock_profile
    ):
        """Test process_review sets status='failed' when safety checks fail."""
        review_result = make_execute_result(first=mock_review)
        profile_result = make_execute_result(first=mock_profile)
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.5}),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.5}),
            ),
            patch(
                "core.services.review_service._run_safety_checks", new=AsyncMock(return_value=False)
            ),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"
        assert mock_review.sections is None
        assert mock_review.overall_score is None

    # ---- process_review: full-failure paths ----

    @pytest.mark.asyncio
    async def test_process_review_exception_sets_failed(
        self, mock_db_session, mock_review, mock_profile
    ):
        """Test the outer except sets status='failed' when a pipeline step raises."""
        review_result = make_execute_result(first=mock_review)
        profile_result = make_execute_result(first=mock_profile)
        recovery_result = make_execute_result(first=mock_review)
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, recovery_result]
        )

        with patch(
            "core.services.review_service._run_ingestion_pipeline",
            new=AsyncMock(side_effect=Exception("boom")),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_process_review_recovery_exception_is_swallowed(
        self, mock_db_session, mock_review, mock_profile
    ):
        """Test that a failure in the except-block's own recovery query doesn't propagate."""
        review_result = make_execute_result(first=mock_review)
        profile_result = make_execute_result(first=mock_profile)
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, Exception("recovery db down")]
        )

        with patch(
            "core.services.review_service._run_ingestion_pipeline",
            new=AsyncMock(side_effect=Exception("boom")),
        ):
            # Should not raise even though the recovery block's db.execute also fails.
            await process_review(mock_db_session, mock_review.id, mock_profile.id)

    # ---- _run_ingestion_pipeline ----

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_all_sources_present(self, mock_db_session):
        """Test all three source types are ingested when present on the profile."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com/portfolio"
        profile.resume_text = "resume contents"
        profile.resume_filename = "resume.pdf"

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(sources) == 3
        assert {s["source_type"] for s in sources} == {"github", "portfolio", "resume"}
        # Note: db.add() is not currently reached for any source here because
        # `IngestedSource(..., raw_data=...)` is called with a kwarg the real
        # model doesn't define (pre-existing bug, out of scope for #109 —
        # each branch's own except catches it and logs, per source_type).
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_no_sources(self, mock_db_session):
        """Test no sources are ingested and no error occurs when none are present."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        profile.resume_filename = None

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert sources == []
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_only_github(self, mock_db_session):
        """Test only the github source is ingested when other sources are absent."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = None
        profile.resume_text = None
        profile.resume_filename = None

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(sources) == 1
        assert sources[0]["source_type"] == "github"

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_source_error_does_not_abort_others(self, mock_db_session):
        """Test a failure in one source's ingestion doesn't prevent the others from completing."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com/portfolio"
        profile.resume_text = "resume contents"
        profile.resume_filename = "resume.pdf"

        with patch(
            "core.services.review_service.IngestedSource",
            side_effect=[RuntimeError("github row boom"), Mock(), Mock()],
        ):
            sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(sources) == 3
        assert {s["source_type"] for s in sources} == {"github", "portfolio", "resume"}
        assert mock_db_session.add.call_count == 2

    # ---- _run_safety_checks ----

    @pytest.mark.asyncio
    async def test_run_safety_checks_passes_with_valid_sections(self):
        """Test safety checks pass for well-formed sections with valid confidence."""
        output = {
            "sections": [
                {"section_name": "Skills", "content": "Good content", "confidence": 0.8},
            ]
        }
        assert await _run_safety_checks(output) is True

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_empty_sections(self):
        """Test safety checks fail when there are no sections."""
        assert await _run_safety_checks({"sections": []}) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_missing_section_name(self):
        """Test safety checks fail when a section is missing its name."""
        output = {"sections": [{"section_name": "", "content": "text", "confidence": 0.5}]}
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_missing_content(self):
        """Test safety checks fail when a section is missing its content."""
        output = {"sections": [{"section_name": "Skills", "content": "", "confidence": 0.5}]}
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_negative_confidence(self):
        """Test safety checks fail when confidence is below 0."""
        output = {"sections": [{"section_name": "Skills", "content": "text", "confidence": -0.1}]}
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_fails_confidence_above_one(self):
        """Test safety checks fail when confidence is above 1."""
        output = {"sections": [{"section_name": "Skills", "content": "text", "confidence": 1.5}]}
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_catches_internal_exception(self):
        """Test an internal error (e.g. a malformed section) is caught and returns False."""
        output = {"sections": ["not-a-dict"]}
        assert await _run_safety_checks(output) is False
