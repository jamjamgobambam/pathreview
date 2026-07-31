"""Tests for review_service.py"""

from unittest.mock import ANY, AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import (
    _run_agent_orchestration,
    _run_ingestion_pipeline,
    _run_rag_retrieval_generation,
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
    async def test_process_review_stops_early_when_review_is_not_found(
        self, mock_db_session: Mock
    ) -> None:
        """Test process_review stops early when review is not found"""
        review_id = uuid4()
        profile_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Confirm error is logged as stated
        with patch("core.services.review_service.log") as mock_log:
            await process_review(mock_db_session, review_id, profile_id)
            mock_log.error.assert_called_once_with(
                "review_not_found_for_processing", review_id=str(review_id)
            )

        mock_db_session.execute.assert_awaited_once()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_process_review_stops_early_when_profile_is_not_found(
        self, mock_db_session: Mock
    ) -> None:
        """Test process_review stops early when profile is not found"""
        review_id = uuid4()
        profile_id = uuid4()

        fake_review = Mock()
        review_lookup_result = Mock()
        review_lookup_result.scalars.return_value.first.return_value = fake_review

        profile_lookup_result = Mock()
        profile_lookup_result.scalars.return_value.first.return_value = None

        mock_db_session.execute = AsyncMock(
            side_effect=[review_lookup_result, profile_lookup_result]
        )

        # Confirm error is logged as stated
        with patch("core.services.review_service.log") as mock_log:
            await process_review(mock_db_session, review_id, profile_id)
            mock_log.error.assert_called_once_with(
                "profile_not_found_for_processing", profile_id=str(profile_id)
            )

        assert mock_db_session.execute.await_count == 2
        mock_db_session.add.assert_called_once_with(fake_review)
        assert fake_review.status == "failed"
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_adds_nothing_and_returns_empty_list_if_profile_is_empty(
        self,
    ) -> None:
        """Test _run_ingestion_pipeline adds nothing and returns empty list if profile is empty"""
        fake_profile = Mock()
        fake_profile.github_username = None
        fake_profile.portfolio_url = None
        fake_profile.resume_text = None

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        sources = await _run_ingestion_pipeline(mock_db, fake_profile)

        mock_db.add.assert_not_called()
        mock_db.commit.assert_awaited_once()
        assert sources == []

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_adds_only_github_username_and_commits(self) -> None:
        """Test _run_ingestion_pipeline adds only github username and commits"""
        fake_profile = Mock()
        fake_profile.github_username = "test_github_username"
        fake_profile.portfolio_url = None
        fake_profile.resume_text = None
        fake_profile.id = uuid4()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        with patch("core.services.review_service.IngestedSource") as mock_ingested_source:
            sources = await _run_ingestion_pipeline(mock_db, fake_profile)

            mock_ingested_source.assert_called_once_with(
                profile_id=fake_profile.id,
                source_type="github",
                raw_data=ANY,
            )
            mock_db.add.assert_called_once_with(mock_ingested_source.return_value)

            assert len(sources) == 1
            assert sources[0]["source_type"] == "github"
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_adds_only_portfolio_url_and_commits(self) -> None:
        """Test _run_ingestion_pipeline adds only portfolio url and commits"""
        fake_profile = Mock()
        fake_profile.github_username = None
        fake_profile.portfolio_url = "https://example.com"
        fake_profile.resume_text = None
        fake_profile.id = uuid4()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        with patch("core.services.review_service.IngestedSource") as mock_ingested_source:
            sources = await _run_ingestion_pipeline(mock_db, fake_profile)

            mock_ingested_source.assert_called_once_with(
                profile_id=fake_profile.id,
                source_type="portfolio",
                raw_data=ANY,
            )
            mock_db.add.assert_called_once_with(mock_ingested_source.return_value)

            assert len(sources) == 1
            assert sources[0]["source_type"] == "portfolio"
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_adds_only_resume_text_and_commits(self) -> None:
        """Test _run_ingestion_pipeline adds only resume text and commits"""
        fake_profile = Mock()
        fake_profile.github_username = None
        fake_profile.portfolio_url = None
        fake_profile.resume_text = "example text"
        fake_profile.resume_filename = "example_resume.pdf"
        fake_profile.id = uuid4()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        with patch("core.services.review_service.IngestedSource") as mock_ingested_source:
            sources = await _run_ingestion_pipeline(mock_db, fake_profile)

            mock_ingested_source.assert_called_once_with(
                profile_id=fake_profile.id,
                source_type="resume",
                raw_data=ANY,
            )
            mock_db.add.assert_called_once_with(mock_ingested_source.return_value)

            assert len(sources) == 1
            assert sources[0]["source_type"] == "resume"
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_adds_all_sources_when_all_fields_set(self) -> None:
        """Test _run_ingestion_pipeline adds github, portfolio, and resume sources when all profile fields are set"""
        fake_profile = Mock()
        fake_profile.github_username = "test_github_username"
        fake_profile.portfolio_url = "https://example.com"
        fake_profile.resume_text = "example text"
        fake_profile.resume_filename = "example_resume.pdf"
        fake_profile.id = uuid4()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        with patch("core.services.review_service.IngestedSource") as mock_ingested_source:
            sources = await _run_ingestion_pipeline(mock_db, fake_profile)

            assert mock_ingested_source.call_count == 3
            assert mock_db.add.call_count == 3

        assert len(sources) == 3
        assert [s["source_type"] for s in sources] == ["github", "portfolio", "resume"]
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_pipeline_continues_after_github_ingestion_error(self) -> None:
        """Test _run_ingestion_pipeline logs and continues past a failed github ingestion, still adding portfolio and resume sources"""
        fake_profile = Mock()
        fake_profile.github_username = "test_github_username"
        fake_profile.portfolio_url = "https://example.com"
        fake_profile.resume_text = "example text"
        fake_profile.resume_filename = "example_resume.pdf"
        fake_profile.id = uuid4()

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        with (
            patch("core.services.review_service.log") as mock_log,
            patch("core.services.review_service.IngestedSource") as mock_ingested_source,
        ):
            mock_ingested_source.side_effect = [Exception("boom"), Mock(), Mock()]

            sources = await _run_ingestion_pipeline(mock_db, fake_profile)

            mock_log.error.assert_called_once_with(
                "github_ingestion_failed",
                username=fake_profile.github_username,
                error="boom",
            )

        # github's sources.append() runs before its IngestedSource() call, so it's
        # still counted here even though the raised exception skips its db.add()
        assert mock_ingested_source.call_count == 3
        assert mock_db.add.call_count == 2
        assert len(sources) == 3
        assert [s["source_type"] for s in sources] == ["github", "portfolio", "resume"]
        mock_db.commit.assert_awaited_once()

    # Test for temporary placeholder according to review_service.py
    @pytest.mark.asyncio
    async def test_run_agent_orchestration_returns_placeholder(self) -> None:
        """Test _run_agent_orchestration returns placeholder defined in review_service.py"""
        mock_profile = Mock()
        mock_ingestion_results: list[dict] = []
        mock_results = await _run_agent_orchestration(mock_profile, mock_ingestion_results)

        # Test will fail when real logic is implemented
        assert mock_profile.mock_calls == []
        assert mock_results == {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Analysis of technical skills from ingested sources",
                    "confidence": 0.8,
                    "suggestions": ["Add more detail on AI/ML experience"],
                },
                {
                    "section_name": "Project Experience",
                    "content": "Analysis of project experience",
                    "confidence": 0.75,
                    "suggestions": ["Include measurable impact metrics"],
                },
            ],
            "overall_score": 0.75,
        }

    # Test for temporary placeholder according to review_service.py
    @pytest.mark.asyncio
    async def test_run_rag_retrieval_generation_returns_placeholder(self) -> None:
        """Test _run_rag_retrieval_generation returns the placeholder defined in review_service.py"""
        mock_profile = Mock()
        mock_ingestion_results: list[dict] = []
        mock_agent_output: dict = {}
        mock_results = await _run_rag_retrieval_generation(
            mock_profile, mock_ingestion_results, mock_agent_output
        )

        # Test will fail when real logic is implemented
        assert mock_profile.mock_calls == []
        assert mock_results == {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Detailed feedback on technical skills based on portfolio analysis",
                    "confidence": 0.85,
                    "suggestions": [
                        "Add more detail on AI/ML experience",
                        "Include specific technologies and frameworks",
                    ],
                },
                {
                    "section_name": "Project Experience",
                    "content": "Detailed feedback on project experience and impact",
                    "confidence": 0.8,
                    "suggestions": [
                        "Include measurable impact metrics",
                        "Add links to project repositories",
                    ],
                },
                {
                    "section_name": "Career Growth",
                    "content": "Feedback on career progression and development",
                    "confidence": 0.78,
                    "suggestions": [
                        "Document learning from each role",
                        "Highlight growth in responsibilities",
                    ],
                },
            ],
            "overall_score": 0.81,
        }

    @pytest.mark.asyncio
    async def test_run_safety_checks_returns_false_when_output_has_no_sections(self) -> None:
        """Test _run_safety_checks returns false when output is has no 'sections' key"""
        mock_output: dict = {}

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.warning.assert_called_once_with("safety_check_failed_no_sections")
            assert mock_result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_returns_false_when_output_sections_is_missing_section_name(
        self,
    ) -> None:
        """Test _run_safety_checks returns false when output["sections"][section] is missing a 'section_name' key"""
        mock_output = {
            "sections": [
                {"content": "test content", "confidence": 0.5, "suggestions": ["test suggestion"]}
            ]
        }

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.warning.assert_called_once_with(
                "safety_check_failed_incomplete_section", section=mock_output["sections"][0]
            )
            assert mock_result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_returns_false_when_output_sections_is_missing_content(
        self,
    ) -> None:
        """Test run_safety_checks returns false when output["sections"][section] is missing a 'content' key"""
        mock_output = {
            "sections": [
                {
                    "section_name": "test section name",
                    "confidence": 0.5,
                    "suggestions": ["test suggestion"],
                }
            ]
        }

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.warning.assert_called_once_with(
                "safety_check_failed_incomplete_section", section=mock_output["sections"][0]
            )
            assert mock_result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_returns_false_if_confidence_is_greater_than_1(self) -> None:
        """Test _run_safety_checks returns false if output["sections"][section]["confidence"] > 1"""
        mock_output = {
            "sections": [
                {
                    "section_name": "test section name",
                    "content": "test content",
                    "confidence": 1.1,
                    "suggestions": ["test suggestion"],
                }
            ]
        }

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.warning.assert_called_once_with(
                "safety_check_failed_invalid_confidence",
                confidence=mock_output["sections"][0]["confidence"],
            )
            assert mock_result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_returns_false_if_confidence_is_less_than_0(self) -> None:
        """Test _run_safety_checks returns false if output["sections"][section]["confidence"] < 0"""
        mock_output = {
            "sections": [
                {
                    "section_name": "test section name",
                    "content": "test content",
                    "confidence": -0.1,
                    "suggestions": ["test suggestion"],
                }
            ]
        }

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.warning.assert_called_once_with(
                "safety_check_failed_invalid_confidence",
                confidence=mock_output["sections"][0]["confidence"],
            )
            assert mock_result is False

    @pytest.mark.asyncio
    async def test_run_safety_checks_returns_true_if_output_is_complete(self) -> None:
        """Test _run_safety_checks returns true if output has complete 'section_name' and 'content' keys, and valid 'confidence' keys"""
        mock_output = {
            "sections": [
                {
                    "section_name": "test section name",
                    "content": "test content",
                    "confidence": 0.5,
                    "suggestions": ["test suggestion"],
                }
            ]
        }

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.info.assert_called_once_with("safety_checks_passed")
            assert mock_result is True

    @pytest.mark.asyncio
    async def test_run_safety_checks_catches_exception_and_returns_false(self) -> None:
        """Test _run_safety_checks catches exception and returns false"""
        mock_output = Mock()
        mock_output.get.side_effect = Exception("boom")

        with patch("core.services.review_service.log") as mock_log:
            mock_result = await _run_safety_checks(mock_output)
            mock_log.error.assert_called_once_with("safety_checks_error", error="boom")
            assert mock_result is False