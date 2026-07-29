"""Tests for the POST /reviews flow — issue #88.

Reproduction for issue #88:
    "POST /reviews endpoint has no test for when the profile has no
     ingested documents"
    https://github.com/ascherj/pathreview/issues/88

Context
-------
When a review is created for a profile that has zero ingested documents
(no github_username, no portfolio_url, no resume_text), the ingestion
pipeline returns an empty source list. However, `process_review` never
checks whether ingestion produced anything: `_run_agent_orchestration`
and `_run_rag_retrieval_generation` return hard-coded placeholder
sections regardless of input, so the review is still marked "complete"
with fabricated feedback and a non-null overall_score.

The two tests below pin down that gap:
  * `test_empty_profile_ingests_zero_sources` documents the confirmed
    root cause — ingestion yields 0 sources for an empty profile.
  * `test_empty_document_profile_should_not_fabricate_review` expresses
    the DESIRED behavior and is marked xfail until the Week 9 fix lands
    (see PLAN.md). It currently fails because the review is fabricated.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from core.services.review_service import _run_ingestion_pipeline, process_review


def _make_empty_profile():
    """A profile with no ingestable sources of any kind."""
    profile = Mock()
    profile.id = uuid4()
    profile.user_id = uuid4()
    profile.github_username = None
    profile.portfolio_url = None
    profile.resume_text = None
    profile.resume_filename = None
    return profile


def _make_pending_review():
    review = Mock()
    review.id = uuid4()
    review.status = "pending"
    review.sections = None
    review.overall_score = None
    return review


def _make_db(review, profile):
    """Mock async session. `process_review` runs select(Review) then
    select(Profile); use plain Mock results so `.scalars().first()` is sync."""
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()

    review_result = Mock()
    review_result.scalars.return_value.first.return_value = review
    profile_result = Mock()
    profile_result.scalars.return_value.first.return_value = profile
    db.execute = AsyncMock(side_effect=[review_result, profile_result])
    return db


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_profile_ingests_zero_sources():
    """Root cause: ingestion yields 0 sources for an empty-document profile."""
    profile = _make_empty_profile()
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()

    sources = await _run_ingestion_pipeline(db, profile)

    assert sources == []


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="issue #88: process_review fabricates a complete review for a "
    "profile with zero ingested documents instead of surfacing the empty "
    "state. Fix planned in Week 9 (see PLAN.md).",
    strict=True,
)
async def test_empty_document_profile_should_not_fabricate_review():
    """DESIRED behavior: an empty-document profile must NOT yield a
    'complete' review full of fabricated sections.

    Currently FAILS (xfail): process_review marks the review 'complete'
    with 3 placeholder sections and overall_score=0.81.
    """
    profile = _make_empty_profile()
    review = _make_pending_review()
    db = _make_db(review, profile)

    await process_review(db, review.id, profile.id)

    # A profile with no documents should not produce fabricated feedback.
    assert review.status != "complete", (
        f"empty-document profile produced status={review.status!r} with "
        f"{len(review.sections or [])} sections and score={review.overall_score}"
    )
