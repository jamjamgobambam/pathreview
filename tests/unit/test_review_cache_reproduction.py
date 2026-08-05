"""Tests for the review caching layer — issue #32.

https://github.com/ascherj/pathreview/issues/32

Before the fix, ``process_review`` re-ran the entire RAG pipeline on every
submission, even for an unchanged portfolio. These tests lock in the caching
behavior:

* the profile content hash is deterministic and content-sensitive;
* an identical resubmission (cache hit) reuses the stored review WITHOUT
  re-running the RAG pipeline — this is the original reproduction, now passing;
* a first/changed submission (cache miss) runs the pipeline and persists the
  hash so the next identical submission can hit the cache.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services import review_service
from core.services.review_service import compute_profile_content_hash


def _result_for(obj: object) -> Mock:
    """Build a mock SQLAlchemy result whose ``.scalars().first()`` returns ``obj``."""
    result = Mock()
    result.scalars.return_value.first.return_value = obj
    return result


def _make_profile() -> Mock:
    """Build a profile with fixed, hashable content fields."""
    profile = Mock()
    profile.id = uuid4()
    profile.github_username = "janedoe"
    profile.portfolio_url = "https://janedoe.dev"
    profile.resume_text = "Software Engineer with 3 years of Python experience."
    profile.resume_filename = "jane_doe_resume.pdf"
    return profile


@pytest.mark.unit
class TestProfileContentHash:
    """Unit tests for compute_profile_content_hash."""

    def test_hash_is_deterministic_for_identical_content(self) -> None:
        """Two profiles with identical content produce the same hash."""
        assert compute_profile_content_hash(_make_profile()) == (
            compute_profile_content_hash(_make_profile())
        )

    def test_hash_is_64_char_hex(self) -> None:
        """The hash is a SHA-256 hex digest."""
        digest = compute_profile_content_hash(_make_profile())
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_hash_changes_when_any_content_field_changes(self) -> None:
        """A single-character change to resume text yields a different hash."""
        base = _make_profile()
        changed = _make_profile()
        changed.resume_text = base.resume_text + "!"
        assert compute_profile_content_hash(base) != compute_profile_content_hash(changed)

    def test_hash_handles_all_none_fields(self) -> None:
        """A profile with no content still hashes without raising."""
        empty = Mock()
        empty.github_username = None
        empty.portfolio_url = None
        empty.resume_text = None
        empty.resume_filename = None
        assert len(compute_profile_content_hash(empty)) == 64


@pytest.mark.unit
class TestProcessReviewCaching:
    """Cache hit/miss behavior in process_review."""

    def _make_db(self, review: Mock, profile: Mock) -> AsyncMock:
        """A db whose two execute() calls return the review then the profile."""
        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.execute = AsyncMock(side_effect=[_result_for(review), _result_for(profile)])
        return db

    @pytest.mark.asyncio
    async def test_cache_hit_skips_pipeline_and_reuses_result(self) -> None:
        """An identical resubmission reuses the cached review, not the pipeline."""
        profile = _make_profile()
        review = Mock()
        review.id = uuid4()
        review.status = "pending"

        cached = Mock()
        cached.id = uuid4()
        cached.sections = [{"section_name": "Skills", "content": "Cached feedback"}]
        cached.overall_score = 0.9

        db = self._make_db(review, profile)

        with (
            patch.object(review_service, "_find_cached_review", new=AsyncMock(return_value=cached)),
            patch.object(
                review_service, "_run_rag_retrieval_generation", new=AsyncMock()
            ) as mock_rag,
        ):
            await review_service.process_review(db, review.id, profile.id)

        # The expensive RAG step must NOT run on a cache hit.
        mock_rag.assert_not_called()
        # The current review is completed with the cached output.
        assert review.status == "complete"
        assert review.sections == cached.sections
        assert review.overall_score == cached.overall_score
        assert review.content_hash == compute_profile_content_hash(profile)

    @pytest.mark.asyncio
    async def test_cache_miss_runs_pipeline_and_persists_hash(self) -> None:
        """A cache miss runs the pipeline once and stores the content hash."""
        profile = _make_profile()
        review = Mock()
        review.id = uuid4()
        review.status = "pending"

        db = self._make_db(review, profile)

        rag_output = {
            "sections": [
                {
                    "section_name": "Skills",
                    "content": "Fresh feedback",
                    "confidence": 0.8,
                    "suggestions": [],
                }
            ],
            "overall_score": 0.8,
        }

        with (
            patch.object(review_service, "_find_cached_review", new=AsyncMock(return_value=None)),
            patch.object(review_service, "_run_ingestion_pipeline", new=AsyncMock(return_value=[])),
            patch.object(
                review_service,
                "_run_agent_orchestration",
                new=AsyncMock(return_value={"sections": []}),
            ),
            patch.object(
                review_service,
                "_run_rag_retrieval_generation",
                new=AsyncMock(return_value=rag_output),
            ) as mock_rag,
            patch.object(review_service, "_run_safety_checks", new=AsyncMock(return_value=True)),
        ):
            await review_service.process_review(db, review.id, profile.id)

        # Pipeline runs exactly once on a miss, and the hash is persisted so the
        # next identical submission becomes a cache hit.
        mock_rag.assert_called_once()
        assert review.status == "complete"
        assert review.content_hash == compute_profile_content_hash(profile)
