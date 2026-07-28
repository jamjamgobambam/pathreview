"""Reproduction for issue #32 — caching layer for repeated identical portfolio queries.

https://github.com/ascherj/pathreview/issues/32

The bug/gap: ``process_review`` in ``core/services/review_service.py`` re-runs the
entire RAG pipeline every time it is called, even when the same profile is
submitted twice with no content changes. There is no content-hash cache, so the
expensive ``_run_rag_retrieval_generation`` step executes on every submission.

This test documents the reproduction. It is marked ``xfail(strict=True)``: it
FAILS today (proving the missing cache) and will XPASS once the caching layer
lands in Week 9 — at which point the marker should be removed.

Reproduction steps:
    1. Build one unchanged profile.
    2. Call ``process_review`` twice with identical inputs.
    3. Observe the expensive RAG step runs on BOTH calls (call_count == 2),
       whereas a cache should make the second call reuse the stored review
       (expected call_count == 1).
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services import review_service


def _result_for(obj: object) -> Mock:
    """Build a mock SQLAlchemy result whose ``.scalars().first()`` returns ``obj``."""
    result = Mock()
    result.scalars.return_value.first.return_value = obj
    return result


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Issue #32: no caching layer yet — identical submissions re-run the "
    "full RAG pipeline. Remove this marker when the cache lands.",
    strict=True,
)
async def test_identical_resubmission_should_not_rerun_rag_pipeline() -> None:
    """An unchanged profile submitted twice should only run RAG generation once."""
    profile_id = uuid4()

    # A single, unchanged profile (identical content on both submissions).
    profile = Mock()
    profile.id = profile_id
    profile.github_username = "janedoe"
    profile.portfolio_url = "https://janedoe.dev"
    profile.resume_text = "Software Engineer with 3 years of Python experience."
    profile.resume_filename = "jane_doe_resume.pdf"

    def fresh_review() -> Mock:
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        return review

    # process_review issues two execute() calls per invocation: fetch Review,
    # then fetch Profile. Feed those lookups for two identical submissions.
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _result_for(fresh_review()),  # 1st submission: Review lookup
            _result_for(profile),  # 1st submission: Profile lookup
            _result_for(fresh_review()),  # 2nd submission: Review lookup
            _result_for(profile),  # 2nd submission: Profile lookup
        ]
    )

    rag_output = {
        "sections": [
            {"section_name": "Skills", "content": "Feedback", "confidence": 0.8, "suggestions": []},
        ],
        "overall_score": 0.8,
    }

    with (
        patch.object(review_service, "_run_ingestion_pipeline", new=AsyncMock(return_value=[])),
        patch.object(
            review_service, "_run_agent_orchestration", new=AsyncMock(return_value={"sections": []})
        ),
        patch.object(
            review_service, "_run_rag_retrieval_generation", new=AsyncMock(return_value=rag_output)
        ) as mock_rag,
        patch.object(review_service, "_run_safety_checks", new=AsyncMock(return_value=True)),
    ):

        # Two identical submissions of the same unchanged profile.
        await review_service.process_review(db, uuid4(), profile_id)
        await review_service.process_review(db, uuid4(), profile_id)

        # A cache keyed on the profile content hash should short-circuit the
        # second run, so the expensive RAG step should execute exactly once.
        # TODAY this is 2 (no cache) -> the test fails, reproducing issue #32.
        assert mock_rag.call_count == 1, (
            f"Expected RAG generation to run once (cache hit on 2nd identical "
            f"submission), but it ran {mock_rag.call_count} times — no caching layer."
        )
