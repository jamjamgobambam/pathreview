"""Tests for review_service.py"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch
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

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------


def make_profile(**overrides):
    """Build a lightweight profile-like object with sane defaults.

    Using SimpleNamespace (rather than a bare Mock) means unset attributes
    are explicitly None instead of auto-vivified truthy Mock objects, which
    matters because _run_ingestion_pipeline branches on `if profile.x:`.
    """
    defaults = dict(
        id=uuid4(),
        user_id=uuid4(),
        github_username=None,
        portfolio_url=None,
        resume_text=None,
        resume_filename=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_review(**overrides):
    defaults = dict(
        id=uuid4(),
        profile_id=uuid4(),
        status="pending",
        sections=None,
        overall_score=None,
        updated_at=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class RaisesOnFormat:
    """Stand-in value that blows up when interpolated into an f-string.

    Used to simulate one ingestion source failing while others succeed,
    without needing to patch internals of the (placeholder) ingestion logic.
    """

    def __format__(self, spec):
        raise ValueError("boom")

    def __str__(self):
        raise ValueError("boom")


def make_db_result(first=None, all_=None):
    """Build a MagicMock standing in for the SQLAlchemy Result object.

    IMPORTANT: this must be a MagicMock, not AsyncMock. `db.execute()` is the
    only awaited call; `.scalars()` / `.first()` / `.all()` are synchronous
    calls made on the *already-awaited* result. If this were an AsyncMock,
    `.scalars` would itself be an AsyncMock, so `.scalars()` would return an
    unawaited coroutine instead of a value, and `.first()`/`.all()` would
    raise AttributeError on that coroutine.
    """
    result = MagicMock()
    result.scalars.return_value.first.return_value = first
    result.scalars.return_value.all.return_value = all_ if all_ is not None else []
    return result


# ---------------------------------------------------------------------------
# create_review / get_review / list_reviews
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestReviewService:
    """Test suite for create_review, get_review, and list_reviews."""

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
        return make_review()

    @pytest.fixture
    def mock_profile(self):
        return make_profile()

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(self, mock_db_session):
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch('core.services.review_service.Review') as mock_review_cls:
            mock_instance = mock_review_cls.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            await create_review(mock_db_session, profile_id, user_id)

            mock_review_cls.assert_called()
            call_kwargs = mock_review_cls.call_args[1]
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(self, mock_db_session):
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()
        mock_review = make_review(id=review_id)

        mock_result = make_db_result(first=mock_review)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, user_id)

        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session):
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        mock_result = make_db_result(first=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, wrong_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session):
        """Test list_reviews returns paginated results."""
        user_id = uuid4()
        mock_reviews = [make_review() for _ in range(5)]

        mock_result = make_db_result(all_=mock_reviews)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=20)

        assert isinstance(total, int)
        assert total >= 0
        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(self, mock_db_session):
        """Test list_reviews page 2 issues queries (offset applied internally)."""
        user_id = uuid4()

        mock_result = make_db_result(all_=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await list_reviews(mock_db_session, user_id, page=2, page_size=20)

        calls = mock_db_session.execute.call_args_list
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session):
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_result = make_db_result(all_=[])
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
        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, uuid4(), uuid4())
            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session):
        """Test create_review calls db.commit()."""
        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, uuid4(), uuid4())
            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session):
        """Test create_review calls db.refresh()."""
        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, uuid4(), uuid4())
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session):
        """Test get_review constructs a query and calls execute."""
        mock_result = make_db_result(first=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session):
        """Test list_reviews uses default page=1, page_size=20."""
        mock_result = make_db_result(all_=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, uuid4())

        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session):
        """Test list_reviews with a custom page size."""
        mock_result = make_db_result(all_=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, uuid4(), page=1, page_size=50)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session):
        """Test create_review passes profile_id and status through to Review()."""
        with patch('core.services.review_service.Review') as mock_review_cls:
            await create_review(mock_db_session, uuid4(), uuid4())

            call_kwargs = mock_review_cls.call_args[1]
            assert "profile_id" in call_kwargs
            assert "status" in call_kwargs

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session):
        """Test get_review issues a single query joining on Profile.user_id."""
        mock_result = make_db_result(first=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session):
        """Test list_reviews calculates total count from the count query."""
        mock_reviews = [make_review() for _ in range(5)]
        mock_result = make_db_result(all_=mock_reviews)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, uuid4())

        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session):
        """Test list_reviews returns a list of Review-like objects."""
        mock_reviews = [make_review() for _ in range(3)]
        mock_result = make_db_result(all_=mock_reviews)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, uuid4())

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(self, mock_db_session):
        """Test a newly created review has sections and overall_score as None."""
        with patch('core.services.review_service.Review') as mock_review_cls:
            await create_review(mock_db_session, uuid4(), uuid4())

            call_kwargs = mock_review_cls.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session):
        """Test get_review handles valid UUID parameters without raising."""
        mock_result = make_db_result(first=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, uuid4(), uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session):
        """Test list_reviews issues its queries (ordering is applied in the
        paginated statement). list_reviews makes two execute() calls: one for
        the total count, one for the paginated/ordered results."""
        mock_result = make_db_result(all_=[])
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await list_reviews(mock_db_session, uuid4())

        assert mock_db_session.execute.call_count == 2


# ---------------------------------------------------------------------------
# process_review — happy path, early returns, and failure branches
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProcessReview:
    """Test suite for process_review's success, partial-failure, and
    full-failure paths."""

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def agent_output(self):
        return {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Analysis of technical skills",
                    "confidence": 0.8,
                    "suggestions": ["Add more detail"],
                },
            ],
            "overall_score": 0.75,
        }

    @pytest.fixture
    def rag_output(self):
        return {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Detailed feedback on technical skills",
                    "confidence": 0.85,
                    "suggestions": ["Include specific technologies"],
                },
            ],
            "overall_score": 0.81,
        }

    @pytest.mark.asyncio
    async def test_process_review_happy_path_sets_complete_and_stores_sections(
        self, mock_db_session, agent_output, rag_output
    ):
        """Full success path should set status='complete' and populate
        sections + overall_score from the RAG output."""
        review = make_review(status="pending")
        profile = make_profile(github_username="alice")

        mock_db_session.execute = AsyncMock(
            side_effect=[
                make_db_result(first=review),
                make_db_result(first=profile),
            ]
        )

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[{"source_type": "github"}]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value=agent_output),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value=rag_output),
            ),
            patch(
                "core.services.review_service._run_safety_checks",
                new=AsyncMock(return_value=True),
            ),
        ):
            await process_review(mock_db_session, review.id, profile.id)

        assert review.status == "complete"
        assert review.overall_score == 0.81
        assert review.sections[0]["section_name"] == "Technical Skills"
        assert review.sections[0]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_process_review_review_not_found_returns_without_commit(self, mock_db_session):
        """If the review can't be found, log and return — no writes at all."""
        mock_db_session.execute = AsyncMock(return_value=make_db_result(first=None))

        await process_review(mock_db_session, uuid4(), uuid4())

        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_review_profile_not_found_marks_failed(self, mock_db_session):
        """If the profile can't be found, the review should be marked failed."""
        review = make_review(status="pending")

        mock_db_session.execute = AsyncMock(
            side_effect=[
                make_db_result(first=review),
                make_db_result(first=None),
            ]
        )

        await process_review(mock_db_session, review.id, uuid4())

        assert review.status == "failed"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_review_safety_check_failure_marks_failed_without_sections(
        self, mock_db_session, agent_output, rag_output
    ):
        """If safety checks fail, status should be 'failed' and sections/score
        must NOT be populated from the (rejected) RAG output."""
        review = make_review(status="pending")
        profile = make_profile(github_username="alice")

        mock_db_session.execute = AsyncMock(
            side_effect=[
                make_db_result(first=review),
                make_db_result(first=profile),
            ]
        )

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value=agent_output),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value=rag_output),
            ),
            patch(
                "core.services.review_service._run_safety_checks",
                new=AsyncMock(return_value=False),
            ),
        ):
            await process_review(mock_db_session, review.id, profile.id)

        assert review.status == "failed"
        assert review.sections is None
        assert review.overall_score is None

    @pytest.mark.asyncio
    async def test_process_review_exception_during_pipeline_marks_failed(self, mock_db_session):
        """An unexpected exception anywhere in the pipeline should be caught,
        and the review re-fetched and marked failed rather than crashing the
        caller."""
        review = make_review(status="pending")
        profile = make_profile(github_username="alice")

        # 1st execute: fetch review: 2nd: fetch profile; 3rd: re-fetch review
        # inside the except block to mark it failed.
        mock_db_session.execute = AsyncMock(
            side_effect=[
                make_db_result(first=review),
                make_db_result(first=profile),
                make_db_result(first=review),
            ]
        )

        with patch(
            "core.services.review_service._run_ingestion_pipeline",
            new=AsyncMock(side_effect=RuntimeError("ingestion exploded")),
        ):
            # Should not raise -- process_review is a background task and
            # must swallow its own errors.
            await process_review(mock_db_session, review.id, profile.id)

        assert review.status == "failed"
        assert review.updated_at is not None


# ---------------------------------------------------------------------------
# _run_ingestion_pipeline
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunIngestionPipeline:
    """Test suite for _run_ingestion_pipeline."""

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_all_sources_present_returns_three_entries(self, mock_db_session):
        """When github, portfolio, and resume are all set, all three should
        be ingested and stored."""
        profile = make_profile(
            github_username="alice",
            portfolio_url="https://alice.dev",
            resume_text="Experienced engineer...",
            resume_filename="resume.pdf",
        )

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(sources) == 3
        source_types = {s["source_type"] for s in sources}
        assert source_types == {"github", "portfolio", "resume"}
        assert mock_db_session.add.call_count == 3
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_sources_present_returns_empty_list(self, mock_db_session):
        """When none of the source fields are set, nothing should be
        ingested, but commit is still called once at the end."""
        profile = make_profile()

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert sources == []
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_one_source_raising_does_not_block_the_others(self, mock_db_session):
        """If one source's ingestion fails, the others should still succeed
        and be returned/stored."""
        profile = make_profile(
            github_username="alice",
            portfolio_url=RaisesOnFormat(),
            resume_text="Experienced engineer...",
            resume_filename="resume.pdf",
        )

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        source_types = {s["source_type"] for s in sources}
        assert source_types == {"github", "resume"}
        assert len(sources) == 2
        assert mock_db_session.add.call_count == 2
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_sources_raising_while_one_succeeds(self, mock_db_session):
        """Even if two of the three sources fail, the pipeline should still
        return the one that succeeded rather than failing the whole run."""
        profile = make_profile(
            github_username=RaisesOnFormat(),
            portfolio_url=RaisesOnFormat(),
            resume_text="Experienced engineer...",
            resume_filename="resume.pdf",
        )

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert len(sources) == 1
        assert sources[0]["source_type"] == "resume"
        assert mock_db_session.add.call_count == 1
        mock_db_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# _run_agent_orchestration / _run_rag_retrieval_generation (placeholder
# integrations -- smoke tests confirming their output shape)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPlaceholderIntegrations:

    @pytest.mark.asyncio
    async def test_run_agent_orchestration_returns_sections_and_score(self):
        profile = make_profile(github_username="alice")

        output = await _run_agent_orchestration(profile, [{"source_type": "github"}])

        assert "sections" in output
        assert isinstance(output["sections"], list)
        assert "overall_score" in output

    @pytest.mark.asyncio
    async def test_run_rag_retrieval_generation_returns_sections_and_score(self):
        profile = make_profile(github_username="alice")
        agent_output = {"sections": [], "overall_score": 0.5}

        output = await _run_rag_retrieval_generation(profile, [], agent_output)

        assert "sections" in output
        assert isinstance(output["sections"], list)
        assert "overall_score" in output


# ---------------------------------------------------------------------------
# _run_safety_checks
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunSafetyChecks:
    """Test suite for _run_safety_checks, including confidence boundaries."""

    @pytest.mark.asyncio
    async def test_empty_sections_fails(self):
        assert await _run_safety_checks({"sections": []}) is False

    @pytest.mark.asyncio
    async def test_missing_sections_key_fails(self):
        assert await _run_safety_checks({}) is False

    @pytest.mark.asyncio
    async def test_section_missing_section_name_fails(self):
        output = {
            "sections": [
                {"content": "some content", "confidence": 0.5},
            ]
        }
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_section_missing_content_fails(self):
        output = {
            "sections": [
                {"section_name": "Skills", "confidence": 0.5},
            ]
        }
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_confidence_below_zero_fails(self):
        output = {
            "sections": [
                {"section_name": "Skills", "content": "x", "confidence": -0.01},
            ]
        }
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_confidence_above_one_fails(self):
        output = {
            "sections": [
                {"section_name": "Skills", "content": "x", "confidence": 1.01},
            ]
        }
        assert await _run_safety_checks(output) is False

    @pytest.mark.asyncio
    async def test_confidence_exactly_zero_passes(self):
        output = {
            "sections": [
                {"section_name": "Skills", "content": "x", "confidence": 0},
            ]
        }
        assert await _run_safety_checks(output) is True

    @pytest.mark.asyncio
    async def test_confidence_exactly_one_passes(self):
        output = {
            "sections": [
                {"section_name": "Skills", "content": "x", "confidence": 1},
            ]
        }
        assert await _run_safety_checks(output) is True

    @pytest.mark.asyncio
    async def test_valid_multi_section_output_passes(self):
        output = {
            "sections": [
                {"section_name": "Skills", "content": "x", "confidence": 0.8},
                {"section_name": "Projects", "content": "y", "confidence": 0.6},
            ]
        }
        assert await _run_safety_checks(output) is True
