"""Tests for review_service.py."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services import review_service


@pytest.mark.unit
class TestReviewService:
    """Test the core review service workflow."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create an async database session mock."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_review(self) -> Mock:
        """Create a review-like object for workflow tests."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        review.updated_at = None
        return review

    @pytest.fixture
    def mock_profile(self) -> Mock:
        """Create a profile-like object for workflow tests."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com"
        profile.resume_text = "resume text"
        profile.resume_filename = "resume.md"
        return profile

    def _build_result(self, value: Any) -> Mock:
        """Build a simple DB result mock with scalars().first()/all()."""
        result = Mock()
        scalars_result = Mock()
        scalars_result.first.return_value = value
        scalars_result.all.return_value = value
        result.scalars.return_value = scalars_result
        return result

    @pytest.mark.asyncio
    async def test_create_review_sets_pending_status_and_commits(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Create a review with pending status and persist it."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_cls:
            review_obj = Mock()
            review_obj.status = "pending"
            review_obj.sections = None
            review_obj.overall_score = None
            mock_review_cls.return_value = review_obj

            result = await review_service.create_review(mock_db_session, profile_id, user_id)

            assert result is review_obj
            mock_review_cls.assert_called_once_with(
                profile_id=profile_id,
                status="pending",
                sections=None,
                overall_score=None,
            )
            mock_db_session.add.assert_called_once_with(review_obj)
            mock_db_session.commit.assert_awaited_once()
            mock_db_session.refresh.assert_awaited_once_with(review_obj)

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_matching_user(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Return a review when it belongs to the current user."""
        review_id = uuid4()
        user_id = uuid4()
        expected_review = Mock()

        mock_db_session.execute = AsyncMock(return_value=self._build_result(expected_review))

        result = await review_service.get_review(mock_db_session, review_id, user_id)

        assert result is expected_review
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results_and_total_count(
        self, mock_db_session: AsyncMock
    ) -> None:
        """List reviews for a user with pagination and total count."""
        user_id = uuid4()
        reviews = [Mock(), Mock()]
        count_result = self._build_result(reviews)
        page_result = self._build_result(reviews)
        mock_db_session.execute = AsyncMock(side_effect=[count_result, page_result])

        result_reviews, total = await review_service.list_reviews(
            mock_db_session, user_id, page=2, page_size=1
        )

        assert result_reviews == reviews
        assert total == 2
        assert mock_db_session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_process_review_completes_successfully_and_stores_sections(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Complete the workflow when ingestion and safety checks succeed."""
        mock_db_session.execute = AsyncMock(
            side_effect=[self._build_result(mock_review), self._build_result(mock_profile)]
        )

        with (
            patch.object(
                review_service,
                "_run_ingestion_pipeline",
                AsyncMock(return_value=[{"source_type": "github"}]),
            ) as ingest_mock,
            patch.object(
                review_service,
                "_run_agent_orchestration",
                AsyncMock(
                    return_value={"sections": [{"section_name": "Skills"}], "overall_score": 0.75}
                ),
            ) as agent_mock,
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                AsyncMock(
                    return_value={
                        "sections": [
                            {
                                "section_name": "Skills",
                                "content": "Great work",
                                "confidence": 0.9,
                                "suggestions": ["Add metrics"],
                            }
                        ],
                        "overall_score": 0.81,
                    }
                ),
            ) as rag_mock,
            patch.object(
                review_service,
                "_run_safety_checks",
                AsyncMock(return_value=True),
            ) as safety_mock,
        ):
            await review_service.process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "complete"
        assert mock_review.overall_score == 0.81
        assert mock_review.sections[0]["section_name"] == "Skills"
        assert mock_review.updated_at is not None
        ingest_mock.assert_awaited_once_with(mock_db_session, mock_profile)
        agent_mock.assert_awaited_once_with(mock_profile, [{"source_type": "github"}])
        rag_mock.assert_awaited_once_with(
            mock_profile,
            [{"source_type": "github"}],
            {"sections": [{"section_name": "Skills"}], "overall_score": 0.75},
        )
        safety_mock.assert_awaited_once_with(
            {
                "sections": [
                    {
                        "section_name": "Skills",
                        "content": "Great work",
                        "confidence": 0.9,
                        "suggestions": ["Add metrics"],
                    }
                ],
                "overall_score": 0.81,
            }
        )

    @pytest.mark.asyncio
    async def test_process_review_marks_review_failed_when_safety_checks_fail(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Mark the review as failed when safety checks reject the output."""
        mock_db_session.execute = AsyncMock(
            side_effect=[self._build_result(mock_review), self._build_result(mock_profile)]
        )

        with (
            patch.object(
                review_service,
                "_run_ingestion_pipeline",
                AsyncMock(return_value=[{"source_type": "github"}]),
            ),
            patch.object(
                review_service,
                "_run_agent_orchestration",
                AsyncMock(
                    return_value={"sections": [{"section_name": "Skills"}], "overall_score": 0.75}
                ),
            ),
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                AsyncMock(
                    return_value={
                        "sections": [
                            {
                                "section_name": "Skills",
                                "content": "Great work",
                                "confidence": 0.9,
                                "suggestions": ["Add metrics"],
                            }
                        ],
                        "overall_score": 0.81,
                    }
                ),
            ),
            patch.object(review_service, "_run_safety_checks", AsyncMock(return_value=False)),
        ):
            await review_service.process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_process_review_marks_review_failed_after_pipeline_exception(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Mark the review failed when a workflow dependency raises unexpectedly."""
        mock_db_session.execute = AsyncMock(
            side_effect=[
                self._build_result(mock_review),
                self._build_result(mock_profile),
                self._build_result(mock_review),
            ]
        )

        with patch.object(
            review_service,
            "_run_ingestion_pipeline",
            AsyncMock(side_effect=RuntimeError("ingestion unavailable")),
        ):
            await review_service.process_review(mock_db_session, mock_review.id, mock_profile.id)

        assert mock_review.status == "failed"
        assert mock_review.updated_at is not None
        assert mock_db_session.execute.await_count == 3
        assert mock_db_session.commit.await_count == 2

    @pytest.mark.asyncio
    async def test_ingestion_pipeline_continues_after_one_source_fails(
        self, mock_db_session: AsyncMock, mock_profile: Mock
    ) -> None:
        """Keep usable sources when storing one ingested source fails."""
        mock_db_session.add.side_effect = [RuntimeError("GitHub storage unavailable"), None, None]

        with patch.object(review_service, "IngestedSource", Mock()):
            results = await review_service._run_ingestion_pipeline(mock_db_session, mock_profile)

        assert [source["source_type"] for source in results] == ["github", "portfolio", "resume"]
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failed_source", ["portfolio", "resume"])
    async def test_ingestion_pipeline_continues_when_later_source_fails(
        self, mock_db_session: AsyncMock, mock_profile: Mock, failed_source: str
    ) -> None:
        """Handle a portfolio or resume ingestion failure without aborting the pipeline."""
        failure_index = {"portfolio": 1, "resume": 2}[failed_source]
        mock_db_session.add.side_effect = [
            RuntimeError("source storage unavailable") if index == failure_index else None
            for index in range(3)
        ]

        with patch.object(review_service, "IngestedSource", Mock()):
            results = await review_service._run_ingestion_pipeline(mock_db_session, mock_profile)

        assert len(results) == 3
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_orchestration_and_rag_helpers_return_review_output(
        self, mock_profile: Mock
    ) -> None:
        """Return the default analysis and generated-feedback structures."""
        sources = [{"source_type": "github"}]

        agent_output = await review_service._run_agent_orchestration(mock_profile, sources)
        rag_output = await review_service._run_rag_retrieval_generation(
            mock_profile, sources, agent_output
        )

        assert agent_output["sections"]
        assert rag_output["sections"]
        assert rag_output["overall_score"] == 0.81

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("output", "expected"),
        [
            ({"sections": []}, False),
            (
                {"sections": [{"section_name": "Skills", "content": "Good", "confidence": 0.8}]},
                True,
            ),
            (
                {"sections": [{"section_name": "", "content": "Good", "confidence": 0.8}]},
                False,
            ),
            (
                {"sections": [{"section_name": "Skills", "content": "Good", "confidence": 1.1}]},
                False,
            ),
        ],
    )
    async def test_safety_checks_validate_review_sections(
        self, output: dict[str, Any], expected: bool
    ) -> None:
        """Accept complete sections and reject incomplete or invalid output."""
        assert await review_service._run_safety_checks(output) is expected

    @pytest.mark.asyncio
    async def test_process_review_marks_review_failed_when_profile_is_missing(
        self, mock_db_session: AsyncMock, mock_review: Mock
    ) -> None:
        """Mark the review as failed when the profile does not exist."""
        mock_db_session.execute = AsyncMock(
            side_effect=[self._build_result(mock_review), self._build_result(None)]
        )

        await review_service.process_review(mock_db_session, mock_review.id, uuid4())

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_process_review_returns_when_review_is_not_found(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Exit early when no review exists for the provided ID."""
        mock_db_session.execute = AsyncMock(return_value=self._build_result(None))

        await review_service.process_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.commit.assert_not_called()
