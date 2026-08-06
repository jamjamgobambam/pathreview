"""Tests for the POST /reviews flow — issue #88.

Issue #88:
    "POST /reviews endpoint has no test for when the profile has no
     ingested documents"
    https://github.com/ascherj/pathreview/issues/88

Context
-------
When a review is created for a profile that has zero ingested documents
(no github_username, no portfolio_url, no resume_text), the ingestion
pipeline returns an empty source list. `_run_agent_orchestration` and
`_run_rag_retrieval_generation` return hard-coded placeholder sections
regardless of their input, so before the fix `process_review` marked such
a review "complete" with fabricated feedback and a non-null overall_score.

`process_review` now stops after ingestion when no sources were produced
and records a terminal `failed` state with an explanatory `error_message`.
These tests cover both the service-level guard and the endpoint behaviour
that exercises it through a background task.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.auth import get_current_user
from api.routes import reviews as reviews_routes
from core.database import get_db
from core.models.review import Review
from core.services.review_service import (
    EMPTY_PROFILE_ERROR_MESSAGE,
    _run_ingestion_pipeline,
    process_review,
)


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


def _make_populated_profile():
    """A profile with at least one ingestable source."""
    profile = _make_empty_profile()
    profile.github_username = "octocat"
    return profile


def _make_pending_review():
    review = Mock()
    review.id = uuid4()
    review.status = "pending"
    review.sections = None
    review.overall_score = None
    review.error_message = None
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
async def test_empty_document_profile_does_not_fabricate_review():
    """An empty-document profile must not yield a 'complete' review."""
    profile = _make_empty_profile()
    review = _make_pending_review()
    db = _make_db(review, profile)

    await process_review(db, review.id, profile.id)

    assert review.status == "failed"
    assert review.sections == []
    assert review.overall_score is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_document_profile_sets_explanatory_error_message():
    """The failure is explained to the user via Review.error_message."""
    profile = _make_empty_profile()
    review = _make_pending_review()
    db = _make_db(review, profile)

    await process_review(db, review.id, profile.id)

    assert review.error_message == EMPTY_PROFILE_ERROR_MESSAGE


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_document_profile_skips_agent_and_rag_steps():
    """The guard short-circuits before any feedback is generated."""
    profile = _make_empty_profile()
    review = _make_pending_review()
    db = _make_db(review, profile)

    with (
        patch(
            "core.services.review_service._run_agent_orchestration",
            new=AsyncMock(),
        ) as agent,
        patch(
            "core.services.review_service._run_rag_retrieval_generation",
            new=AsyncMock(),
        ) as rag,
    ):
        await process_review(db, review.id, profile.id)

    agent.assert_not_called()
    rag.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_string_resume_text_is_treated_as_no_document():
    """An empty-string resume is not a document and follows the empty path."""
    profile = _make_empty_profile()
    profile.resume_text = ""
    review = _make_pending_review()
    db = _make_db(review, profile)

    await process_review(db, review.id, profile.id)

    assert review.status == "failed"
    assert review.error_message == EMPTY_PROFILE_ERROR_MESSAGE


@pytest.mark.unit
@pytest.mark.asyncio
async def test_profile_with_one_source_still_completes():
    """Regression guard: the fix must only affect fully empty profiles."""
    profile = _make_populated_profile()
    review = _make_pending_review()
    db = _make_db(review, profile)

    await process_review(db, review.id, profile.id)

    assert review.status == "complete"
    assert review.sections
    assert review.overall_score is not None


def _build_test_app(db):
    """A minimal app exposing only the reviews router, with auth and the
    database session replaced by test doubles."""
    app = FastAPI()
    app.include_router(reviews_routes.router)

    user = Mock()
    user.id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    return app


@pytest.mark.unit
def test_create_review_endpoint_with_empty_profile_returns_pending_then_fails():
    """POST /reviews returns a pending review immediately; the background
    task then leaves an empty-document profile in the terminal failed state."""
    profile = _make_empty_profile()
    now = datetime.utcnow()
    review = Review(
        id=str(uuid4()),
        profile_id=str(profile.id),
        status="pending",
        sections=None,
        overall_score=None,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    db = _make_db(review, profile)
    app = _build_test_app(db)

    with (
        patch.object(reviews_routes, "create_review", new=AsyncMock(return_value=review)),
        TestClient(app) as client,
    ):
        response = client.post("/reviews", json={"profile_id": str(profile.id)})

    # The endpoint responds before the background task runs.
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    # TestClient runs background tasks before returning, so by now the
    # empty-document profile has been resolved to a truthful terminal state.
    assert review.status == "failed"
    assert review.sections == []
    assert review.overall_score is None
    assert review.error_message == EMPTY_PROFILE_ERROR_MESSAGE
