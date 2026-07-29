"""Reproduction test for issue #82: concurrent review requests for the same
profile are not serialized, so their processing windows can overlap and
interleave against shared profile state.

_run_ingestion_pipeline, _run_agent_orchestration, _run_rag_retrieval_generation,
and _run_safety_checks are patched out because the real ingestion pipeline has
an unrelated, pre-existing bug (IngestedSource is constructed with a `raw_data`
kwarg that isn't a column on the model) that crashes it independent of
concurrency. Patching lets this test isolate exactly what #82 is about: whether
two `process_review` calls for the same profile are allowed to run at the same
time.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.models.profile import Profile
from core.models.review import Review
from core.models.user import User
from core.services.review_service import process_review

Window = tuple[float, float]


async def _slow_ingestion(
    db: AsyncSession,
    profile: Profile,
    windows: dict[str, list[Window]],
    delay: float = 0.2,
) -> list[dict[str, Any]]:
    """Stand-in for _run_ingestion_pipeline that records when it started/finished
    running for a given profile, so overlapping calls can be detected."""
    start = asyncio.get_event_loop().time()
    await asyncio.sleep(delay)
    end = asyncio.get_event_loop().time()
    windows.setdefault(str(profile.id), []).append((start, end))
    return [{"source_type": "github", "data": "stub"}]


def _windows_overlap(a: Window, b: Window) -> bool:
    a_start, a_end = a
    b_start, b_end = b
    return a_start < b_end and b_start < a_end


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def two_reviews_same_profile(
    db_session: AsyncSession,
) -> AsyncGenerator[tuple[Profile, Review, Review], None]:
    """Two Review rows pointing at the same Profile, as created by two
    near-simultaneous POST /reviews calls."""
    user = User(id=str(uuid4()), email=f"{uuid4()}@example.com", hashed_password="x")
    profile = Profile(id=str(uuid4()), user_id=user.id, github_username="octocat")
    review_a = Review(id=str(uuid4()), profile_id=profile.id, status="pending")
    review_b = Review(id=str(uuid4()), profile_id=profile.id, status="pending")

    db_session.add_all([user, profile, review_a, review_b])
    await db_session.commit()

    yield profile, review_a, review_b

    await db_session.execute(delete(Review).where(Review.profile_id == profile.id))
    await db_session.execute(delete(Profile).where(Profile.id == profile.id))
    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.commit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_reviews_for_same_profile_are_not_serialized(
    db_session: AsyncSession,
    two_reviews_same_profile: tuple[Profile, Review, Review],
) -> None:
    """Reproduces #82: without a per-profile lock, two process_review() calls
    for the same profile_id run their ingestion step concurrently instead of
    one waiting for the other."""
    profile, review_a, review_b = two_reviews_same_profile
    windows: dict[str, list[Window]] = {}

    async def fake_ingestion(db: AsyncSession, profile_arg: Profile) -> list[dict[str, Any]]:
        return await _slow_ingestion(db, profile_arg, windows)

    with (
        patch("core.services.review_service._run_ingestion_pipeline", fake_ingestion),
        patch(
            "core.services.review_service._run_agent_orchestration",
            AsyncMock(return_value={"sections": []}),
        ),
        patch(
            "core.services.review_service._run_rag_retrieval_generation",
            AsyncMock(return_value={"sections": [], "overall_score": 1.0}),
        ),
        patch(
            "core.services.review_service._run_safety_checks",
            AsyncMock(return_value=True),
        ),
    ):
        async with AsyncSessionLocal() as db_a, AsyncSessionLocal() as db_b:
            await asyncio.gather(
                process_review(db_a, review_a.id, profile.id),
                process_review(db_b, review_b.id, profile.id),
            )

    profile_windows = windows[str(profile.id)]
    assert len(profile_windows) == 2

    # Today (pre-fix), these two windows overlap because nothing serializes
    # concurrent processing for the same profile. Once a per-profile lock is
    # added, this assertion should be flipped to assert the windows do NOT
    # overlap.
    assert _windows_overlap(*profile_windows), (
        "Expected the current (unfixed) code to allow overlapping ingestion "
        "windows for the same profile_id -- if this fails, a lock may already "
        "be serializing these calls."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_reviews_for_different_profiles_still_run_in_parallel(
    db_session: AsyncSession,
) -> None:
    """Sanity check: two reviews for *different* profiles should be free to run
    concurrently. A future per-profile lock must not become a global lock."""
    user_a = User(id=str(uuid4()), email=f"{uuid4()}@example.com", hashed_password="x")
    user_b = User(id=str(uuid4()), email=f"{uuid4()}@example.com", hashed_password="x")
    profile_a = Profile(id=str(uuid4()), user_id=user_a.id, github_username="octocat-a")
    profile_b = Profile(id=str(uuid4()), user_id=user_b.id, github_username="octocat-b")
    review_a = Review(id=str(uuid4()), profile_id=profile_a.id, status="pending")
    review_b = Review(id=str(uuid4()), profile_id=profile_b.id, status="pending")

    db_session.add_all([user_a, user_b, profile_a, profile_b, review_a, review_b])
    await db_session.commit()

    windows: dict[str, list[Window]] = {}

    async def fake_ingestion(db: AsyncSession, profile_arg: Profile) -> list[dict[str, Any]]:
        return await _slow_ingestion(db, profile_arg, windows)

    try:
        with (
            patch("core.services.review_service._run_ingestion_pipeline", fake_ingestion),
            patch(
                "core.services.review_service._run_agent_orchestration",
                AsyncMock(return_value={"sections": []}),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                AsyncMock(return_value={"sections": [], "overall_score": 1.0}),
            ),
            patch(
                "core.services.review_service._run_safety_checks",
                AsyncMock(return_value=True),
            ),
        ):
            async with AsyncSessionLocal() as db_a, AsyncSessionLocal() as db_b:
                await asyncio.gather(
                    process_review(db_a, review_a.id, profile_a.id),
                    process_review(db_b, review_b.id, profile_b.id),
                )

        window_a = windows[str(profile_a.id)][0]
        window_b = windows[str(profile_b.id)][0]
        assert _windows_overlap(
            window_a, window_b
        ), "Different profiles should be able to process concurrently"
    finally:
        for profile, user in ((profile_a, user_a), (profile_b, user_b)):
            await db_session.execute(delete(Review).where(Review.profile_id == profile.id))
            await db_session.execute(delete(Profile).where(Profile.id == profile.id))
            await db_session.execute(delete(User).where(User.id == user.id))
        await db_session.commit()
