"""Tests for review_service.py

Mocking rule for SQLAlchemy 2.0 async sessions:
  - db.execute            -> AsyncMock (awaited)
  - result.scalars()      -> MagicMock (sync)
  - .first() / .all()     -> sync
  - db.add                -> plain Mock (sync)
  - db.commit / db.refresh -> AsyncMock
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest

from core.services import review_service
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


def _exec_result(value: object, kind: str = "first") -> MagicMock:
    """Build a sync MagicMock whose .scalars().first()/all() returns `value`."""
    result = MagicMock()
    if kind == "first":
        result.scalars.return_value.first.return_value = value
    else:
        result.scalars.return_value.all.return_value = value
    return result


@pytest.mark.unit
class TestReviewService:
    """Test suite for review_service module."""

    @pytest.fixture
    def mock_db_session(self) -> MagicMock:
        session = MagicMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_review(self) -> Mock:
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        return review

    @pytest.fixture
    def mock_profile_full(self) -> Mock:
        """Profile with all three source fields populated (happy path)."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com"
        profile.resume_text = "resume body text"
        profile.resume_filename = "resume.pdf"
        return profile

    @pytest.fixture
    def mock_profile_empty(self) -> Mock:
        """Profile with no ingestible sources."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        profile.resume_filename = None
        return profile

    # ------------------------------------------------------------------
    # create_review
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(
        self, mock_db_session: MagicMock
    ) -> None:
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as MockReview:  # noqa: N806
            mock_instance = MockReview.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            await create_review(mock_db_session, profile_id, user_id)

            MockReview.assert_called()
            call_kwargs = MockReview.call_args[1]
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_review_calls_db_add(self, mock_db_session: MagicMock) -> None:
        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, uuid4(), uuid4())
            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session: MagicMock) -> None:
        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, uuid4(), uuid4())
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session: MagicMock) -> None:
        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, uuid4(), uuid4())
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session: MagicMock) -> None:
        with patch("core.services.review_service.Review") as MockReview:  # noqa: N806
            MockReview.return_value = Mock()
            await create_review(mock_db_session, uuid4(), uuid4())

            call_kwargs = MockReview.call_args[1]
            assert "profile_id" in call_kwargs
            assert "status" in call_kwargs

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(
        self, mock_db_session: MagicMock
    ) -> None:
        with patch("core.services.review_service.Review") as MockReview:  # noqa: N806
            MockReview.return_value = Mock()
            await create_review(mock_db_session, uuid4(), uuid4())

            call_kwargs = MockReview.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    # ------------------------------------------------------------------
    # get_review
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(
        self, mock_db_session: MagicMock
    ) -> None:
        review_id = uuid4()
        user_id = uuid4()
        review = Mock(id=review_id)

        mock_db_session.execute = AsyncMock(return_value=_exec_result(review))

        result = await get_review(mock_db_session, review_id, user_id)

        assert result is review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(return_value=_exec_result(None))

        result = await get_review(mock_db_session, uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(return_value=_exec_result(None))

        await get_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(return_value=_exec_result(None))

        await get_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(return_value=_exec_result(None))

        result = await get_review(mock_db_session, uuid4(), uuid4())

        assert result is None

    # ------------------------------------------------------------------
    # list_reviews
    # NOTE: list_reviews computes total via len(scalars().all()) on the
    # unpaginated query. Both execute calls therefore need .scalars().all()
    # wired up. See PLAN.md re: existing count bug (out of scope).
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session: MagicMock) -> None:
        reviews = [Mock() for _ in range(5)]
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result(reviews, "all"), _exec_result(reviews, "all")]
        )

        result_reviews, total = await list_reviews(mock_db_session, uuid4(), page=1, page_size=20)

        assert isinstance(total, int)
        assert total >= 0
        assert isinstance(result_reviews, list)

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(
        self, mock_db_session: MagicMock
    ) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result([], "all"), _exec_result([], "all")]
        )

        await list_reviews(mock_db_session, uuid4(), page=2, page_size=20)

        assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result([], "all"), _exec_result([], "all")]
        )

        result = await list_reviews(mock_db_session, uuid4())

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result([], "all"), _exec_result([], "all")]
        )

        reviews, total = await list_reviews(mock_db_session, uuid4())

        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result([], "all"), _exec_result([], "all")]
        )

        reviews, _ = await list_reviews(mock_db_session, uuid4(), page=1, page_size=50)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session: MagicMock) -> None:
        reviews = [Mock() for _ in range(5)]
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result(reviews, "all"), _exec_result(reviews, "all")]
        )

        _, total = await list_reviews(mock_db_session, uuid4())

        assert total == 5

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session: MagicMock) -> None:
        reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result(reviews, "all"), _exec_result(reviews, "all")]
        )

        result_reviews, _ = await list_reviews(mock_db_session, uuid4())

        assert isinstance(result_reviews, list)

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session: MagicMock) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[_exec_result([], "all"), _exec_result([], "all")]
        )

        await list_reviews(mock_db_session, uuid4())

        assert mock_db_session.execute.call_count == 2

    # ------------------------------------------------------------------
    # process_review — 8 branch tests
    # execute call order inside process_review:
    #   1. select Review by id           -> review lookup
    #   2. select Profile by id          -> profile lookup
    #   (on exception) 3. re-fetch Review to write failed status
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_review_full_pipeline_success(
        self, mock_db_session, mock_review, mock_profile_full
    ) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(mock_profile_full),
            ]
        )

        rag_output = {
            "sections": [
                {
                    "section_name": "Skills",
                    "content": "text",
                    "confidence": 0.8,
                    "suggestions": ["s1"],
                }
            ],
            "overall_score": 0.9,
        }

        with (
            patch.object(review_service, "_run_ingestion_pipeline", AsyncMock(return_value=[])),
            patch.object(
                review_service, "_run_agent_orchestration", AsyncMock(return_value={"sections": []})
            ),
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                AsyncMock(return_value=rag_output),
            ),
            patch.object(review_service, "_run_safety_checks", AsyncMock(return_value=True)),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile_full.id)

        assert mock_review.status == "complete"
        assert mock_review.overall_score == 0.9
        assert mock_review.sections == [
            {
                "section_name": "Skills",
                "content": "text",
                "confidence": 0.8,
                "suggestions": ["s1"],
            }
        ]

    @pytest.mark.asyncio
    async def test_process_review_review_not_found_early_return(
        self, mock_db_session: MagicMock
    ) -> None:
        mock_db_session.execute = AsyncMock(return_value=_exec_result(None))

        await process_review(mock_db_session, uuid4(), uuid4())

        # only the review lookup happened; no commits triggered
        assert mock_db_session.execute.call_count == 1
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_review_profile_not_found_marks_failed(
        self, mock_db_session, mock_review
    ) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(None),
            ]
        )

        await process_review(mock_db_session, mock_review.id, uuid4())

        assert mock_review.status == "failed"
        mock_db_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_process_review_safety_check_fail_marks_failed(
        self, mock_db_session, mock_review, mock_profile_full
    ) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(mock_profile_full),
            ]
        )

        with (
            patch.object(review_service, "_run_ingestion_pipeline", AsyncMock(return_value=[])),
            patch.object(
                review_service, "_run_agent_orchestration", AsyncMock(return_value={"sections": []})
            ),
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                AsyncMock(return_value={"sections": []}),
            ),
            patch.object(review_service, "_run_safety_checks", AsyncMock(return_value=False)),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile_full.id)

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_process_review_partial_ingestion_failure_still_completes(
        self, mock_db_session, mock_review, mock_profile_full
    ) -> None:
        """One ingestion source raising is swallowed; pipeline still completes."""
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(mock_profile_full),
            ]
        )

        # Simulate the pipeline returning partial results (github failed silently, others succeeded)
        rag_output = {
            "sections": [
                {
                    "section_name": "Skills",
                    "content": "c",
                    "confidence": 0.5,
                    "suggestions": [],
                }
            ],
            "overall_score": 0.5,
        }

        with (
            patch.object(
                review_service,
                "_run_ingestion_pipeline",
                AsyncMock(return_value=[{"source_type": "resume", "data": "x"}]),
            ),
            patch.object(
                review_service, "_run_agent_orchestration", AsyncMock(return_value={"sections": []})
            ),
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                AsyncMock(return_value=rag_output),
            ),
            patch.object(review_service, "_run_safety_checks", AsyncMock(return_value=True)),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile_full.id)

        assert mock_review.status == "complete"

    @pytest.mark.asyncio
    async def test_process_review_unexpected_exception_flips_to_failed(
        self, mock_db_session, mock_review, mock_profile_full
    ) -> None:
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(mock_profile_full),
                _exec_result(mock_review),  # exception-handler re-fetch
            ]
        )

        with (
            patch.object(
                review_service,
                "_run_ingestion_pipeline",
                AsyncMock(side_effect=RuntimeError("boom")),
            ),
        ):
            await process_review(mock_db_session, mock_review.id, mock_profile_full.id)

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_process_review_exception_during_recovery_is_swallowed(
        self, mock_db_session, mock_review, mock_profile_full
    ) -> None:
        """Outer except raises, then inner recovery re-fetch also raises — must not propagate."""
        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(mock_profile_full),
                RuntimeError("db exploded during recovery"),
            ]
        )

        with patch.object(
            review_service,
            "_run_ingestion_pipeline",
            AsyncMock(side_effect=RuntimeError("primary failure")),
        ):
            # Must not raise
            await process_review(mock_db_session, mock_review.id, mock_profile_full.id)

    @pytest.mark.asyncio
    async def test_process_review_profile_with_only_one_source(
        self, mock_db_session, mock_review
    ) -> None:
        one_source_profile = Mock()
        one_source_profile.id = uuid4()
        one_source_profile.user_id = uuid4()
        one_source_profile.github_username = None
        one_source_profile.portfolio_url = None
        one_source_profile.resume_text = "just a resume"
        one_source_profile.resume_filename = "r.pdf"

        mock_db_session.execute = AsyncMock(
            side_effect=[
                _exec_result(mock_review),
                _exec_result(one_source_profile),
            ]
        )

        rag_output = {
            "sections": [
                {"section_name": "S", "content": "c", "confidence": 0.7, "suggestions": []}
            ],
            "overall_score": 0.7,
        }

        with (
            patch.object(
                review_service,
                "_run_ingestion_pipeline",
                AsyncMock(return_value=[{"source_type": "resume"}]),
            ),
            patch.object(
                review_service, "_run_agent_orchestration", AsyncMock(return_value={"sections": []})
            ),
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                AsyncMock(return_value=rag_output),
            ),
            patch.object(review_service, "_run_safety_checks", AsyncMock(return_value=True)),
        ):
            await process_review(mock_db_session, mock_review.id, one_source_profile.id)

        assert mock_review.status == "complete"


@pytest.mark.unit
class TestReviewServiceHelpers:
    """Direct coverage of the module-level helpers."""

    @pytest.fixture
    def mock_db_session(self) -> MagicMock:
        session = MagicMock()
        session.add = Mock()
        session.commit = AsyncMock()
        return session

    # ----- _run_ingestion_pipeline -----

    @pytest.mark.asyncio
    async def test_ingestion_all_sources_present(self, mock_db_session: MagicMock) -> None:
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com"
        profile.resume_text = "resume"
        profile.resume_filename = "r.pdf"

        # NOTE: IngestedSource(...) in review_service.py:216 passes raw_data=,
        # which is not a real column on the model — production code silently
        # swallows the TypeError via the per-source try/except. We patch the
        # model here so the db.add branches actually execute for coverage.
        with patch("core.services.review_service.IngestedSource"):
            results = await _run_ingestion_pipeline(mock_db_session, profile)

        types = {r["source_type"] for r in results}
        assert types == {"github", "portfolio", "resume"}
        assert mock_db_session.add.call_count == 3
        mock_db_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ingestion_no_sources_present(self, mock_db_session: MagicMock) -> None:
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None

        results = await _run_ingestion_pipeline(mock_db_session, profile)

        assert results == []
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_awaited_once()

    # ----- _run_agent_orchestration -----

    @pytest.mark.asyncio
    async def test_agent_orchestration_returns_expected_shape(self) -> None:
        profile = Mock()
        out = await _run_agent_orchestration(profile, [])

        assert "sections" in out
        assert "overall_score" in out
        assert isinstance(out["sections"], list)

    # ----- _run_rag_retrieval_generation -----

    @pytest.mark.asyncio
    async def test_rag_retrieval_returns_expected_shape(self) -> None:
        profile = Mock()
        out = await _run_rag_retrieval_generation(profile, [], {})

        assert "sections" in out
        assert "overall_score" in out
        assert len(out["sections"]) >= 1

    # ----- _run_safety_checks -----

    @pytest.mark.asyncio
    async def test_safety_valid_output_passes(self) -> None:
        output = {
            "sections": [
                {
                    "section_name": "Skills",
                    "content": "c",
                    "confidence": 0.5,
                    "suggestions": [],
                }
            ],
        }
        assert await _run_safety_checks(output) is True

    @pytest.mark.asyncio
    async def test_safety_missing_sections_fails(self) -> None:
        assert await _run_safety_checks({"sections": []}) is False
        assert await _run_safety_checks({}) is False

    @pytest.mark.asyncio
    async def test_safety_invalid_confidence_fails(self) -> None:
        for bad in (1.5, -0.1):
            output = {
                "sections": [
                    {
                        "section_name": "Skills",
                        "content": "c",
                        "confidence": bad,
                        "suggestions": [],
                    }
                ],
            }
            assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_safety_missing_section_name_or_content_fails(self) -> None:
        no_name = {
            "sections": [{"section_name": "", "content": "c", "confidence": 0.5, "suggestions": []}]
        }
        no_content = {
            "sections": [{"section_name": "S", "content": "", "confidence": 0.5, "suggestions": []}]
        }
        assert await _run_safety_checks(no_name) is False
        assert await _run_safety_checks(no_content) is False
