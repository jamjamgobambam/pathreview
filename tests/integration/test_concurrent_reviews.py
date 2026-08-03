"""Reproduction test for GitHub issue #82.

This tests isolation, not deduplication. Submitting two review requests for
the same profile back to back schedules two concurrent process_review()
background tasks. Without a per-profile lock, both tasks' calls into
_run_ingestion_pipeline() -- the only step that touches shared, profile-scoped
DB state -- can run interleaved instead of serialized. This test asserts the
opposite of that: whichever task starts second must not begin its ingestion
work until the first task has fully finished and committed a terminal Review
status. It intentionally does not assert anything about duplicate
IngestedSource rows -- that's a separate concern.

Instrumentation targets _run_ingestion_pipeline() specifically because it is
the only shared-state touchpoint in the current pipeline (steps 3-5 are
stubs that don't read or write the DB). If a future profile lock wraps the
full process_review() body, as the issue asks for, this test still passes --
it's a lower bound on the lock's coverage, not an upper one.

Exercises the real AsyncSession/asyncpg stack rather than mocks, so it's
marked `integration` rather than `unit`. tests/conftest.py starts an
ephemeral Postgres container for the run (requires Docker) and points
DATABASE_URL at it before this module is imported.
"""

import asyncio
import time
import uuid
from unittest.mock import patch

import pytest
from redis.asyncio import Redis as AsyncRedis
from structlog.testing import capture_logs

import core.services.review_service as review_service
from core.database import AsyncSessionLocal
from core.models.profile import Profile
from core.models.review import Review
from core.models.user import User
from core.services.review_service import create_review, process_review


@pytest.mark.integration
@pytest.mark.asyncio
class TestConcurrentReviews:
    async def _make_profile(self) -> tuple[str, str]:
        async with AsyncSessionLocal() as db:
            user = User(email=f"{uuid.uuid4()}@example.com", hashed_password="x")
            db.add(user)
            await db.flush()

            profile = Profile(
                user_id=user.id,
                github_username="octocat",
                portfolio_url="https://example.com/portfolio",
                resume_text="Experienced engineer.",
            )
            db.add(profile)
            await db.commit()
            return user.id, profile.id

    async def _cleanup(self, user_id: str) -> None:
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
            if user:
                await db.delete(user)
                await db.commit()

    async def test_concurrent_reviews_are_serialized_by_profile_lock(self):
        """Two reviews for the same profile must never run concurrently.

        Submits two reviews for one profile via asyncio.gather and asserts
        their ingestion windows never overlap, and that the second review
        only starts once the first is already committed with a terminal
        status.
        """
        user_id, profile_id = await self._make_profile()
        try:
            async with AsyncSessionLocal() as db1, AsyncSessionLocal() as db2:
                review1 = await create_review(db1, profile_id, user_id)
                review2 = await create_review(db2, profile_id, user_id)

                windows = []
                original_ingestion = review_service._run_ingestion_pipeline

                async def instrumented_ingestion(db, profile):
                    this_id = review1.id if db is db1 else review2.id
                    other_id = review2.id if db is db1 else review1.id

                    start = time.monotonic()
                    async with AsyncSessionLocal() as snap_db:
                        other_review = await snap_db.get(Review, other_id)
                        other_status_at_start = other_review.status

                    result = await original_ingestion(db, profile)

                    windows.append(
                        {
                            "review_id": this_id,
                            "other_status_at_start": other_status_at_start,
                            "start": start,
                            "end": time.monotonic(),
                        }
                    )
                    return result

                with patch.object(
                    review_service, "_run_ingestion_pipeline", side_effect=instrumented_ingestion
                ):
                    await asyncio.gather(
                        process_review(db1, review1.id, profile_id),
                        process_review(db2, review2.id, profile_id),
                    )

            assert len(windows) == 2, f"expected both reviews to run ingestion, got {windows}"
            first, second = sorted(windows, key=lambda w: w["start"])

            # No overlap: the second review's ingestion must not start until
            # the first review's ingestion has finished and committed.
            assert first["end"] <= second["start"], (
                "concurrent reviews were not isolated -- ingestion windows overlapped: "
                f"{first} vs {second}"
            )

            # The second review must only begin after the first is already
            # committed with a terminal status -- proof the lock was actually
            # held and released, not just accidentally non-overlapping.
            assert second["other_status_at_start"] in ("complete", "failed"), (
                f"second review began while the first was still "
                f"'{second['other_status_at_start']}', meaning the profile lock was not "
                "held across the first review's full run"
            )

            async with AsyncSessionLocal() as db:
                r1 = await db.get(Review, review1.id)
                r2 = await db.get(Review, review2.id)
            assert {r1.status, r2.status} == {"complete"}
        finally:
            await self._cleanup(user_id)

    async def test_independent_profile_is_not_blocked_by_unrelated_profile_lock(self):
        """A per-profile lock must not degrade into a global one.

        Reviews 1 and 2 share profile A and must serialize exactly like the
        test above. Review 3 lives on an unrelated profile B, submitted at
        the same time. If the eventual lock is correctly scoped per profile,
        review 3's ingestion runs and commits while profile A's lock is still
        held by review 1 -- the idle event loop picks it up instead of
        queueing behind an unrelated profile's lock. If the lock is
        accidentally global, review 3 gets stuck behind review 1 too, and
        this test catches that.
        """
        user_a, profile_a = await self._make_profile()
        user_b, profile_b = await self._make_profile()
        try:
            async with (
                AsyncSessionLocal() as db1,
                AsyncSessionLocal() as db2,
                AsyncSessionLocal() as db3,
            ):
                review1 = await create_review(db1, profile_a, user_a)
                review2 = await create_review(db2, profile_a, user_a)
                review3 = await create_review(db3, profile_b, user_b)

                windows = []
                original_ingestion = review_service._run_ingestion_pipeline

                async def instrumented_ingestion(db, profile):
                    if profile.id == profile_b:
                        this_id, other_id = review3.id, None
                    else:
                        this_id = review1.id if db is db1 else review2.id
                        other_id = review2.id if db is db1 else review1.id

                    start = time.monotonic()
                    other_status_at_start = None
                    if other_id is not None:
                        async with AsyncSessionLocal() as snap_db:
                            other_review = await snap_db.get(Review, other_id)
                            other_status_at_start = other_review.status

                    result = await original_ingestion(db, profile)

                    windows.append(
                        {
                            "review_id": this_id,
                            "other_status_at_start": other_status_at_start,
                            "start": start,
                            "end": time.monotonic(),
                        }
                    )
                    return result

                with patch.object(
                    review_service, "_run_ingestion_pipeline", side_effect=instrumented_ingestion
                ):
                    await asyncio.gather(
                        process_review(db1, review1.id, profile_a),
                        process_review(db2, review2.id, profile_a),
                        process_review(db3, review3.id, profile_b),
                    )

            assert len(windows) == 3, f"expected all three reviews to run ingestion, got {windows}"
            by_id = {w["review_id"]: w for w in windows}
            w1, w2, w3 = by_id[review1.id], by_id[review2.id], by_id[review3.id]

            # Same-profile pair: still strictly serialized, same as the test above.
            first, second = sorted([w1, w2], key=lambda w: w["start"])
            assert first["end"] <= second["start"], (
                "profile A's reviews were not isolated -- ingestion windows overlapped: "
                f"{first} vs {second}"
            )
            assert second["other_status_at_start"] in ("complete", "failed"), (
                f"profile A's second review began while the first was still "
                f"'{second['other_status_at_start']}'"
            )

            # Cross-profile: review3 must make progress (and commit its
            # IngestedSource inserts) *while* profile A's lock is still held,
            # not queue up behind it.
            assert w3["start"] < first["end"], (
                "profile B's review waited for profile A's lock to release before "
                "starting -- this looks like a global lock rather than a per-profile "
                f"lock: {w3} vs {first}"
            )

            async with AsyncSessionLocal() as db:
                r1 = await db.get(Review, review1.id)
                r2 = await db.get(Review, review2.id)
                r3 = await db.get(Review, review3.id)
            assert {r1.status, r2.status, r3.status} == {"complete"}
        finally:
            await self._cleanup(user_a)
            await self._cleanup(user_b)

    async def test_lock_is_released_when_review_processing_raises(self):
        """A review that fails partway through must not hold the lock forever.

        Whichever review wins profile A's lock first has its pipeline made to
        raise partway through (patching _run_agent_orchestration, which runs
        after ingestion). process_review() catches that, marks the review
        "failed", and the `async with` lock must still release -- otherwise
        the other review would hang forever waiting for it, since the lock's
        blocking_timeout is left at its default (block indefinitely).

        Deliberately asserts on the *set* of final statuses rather than
        assuming review1 wins the lock race, since which of the two actually
        acquires it first isn't guaranteed -- only that exactly one fails and
        the other completes.
        """
        user_id, profile_id = await self._make_profile()
        try:
            async with AsyncSessionLocal() as db1, AsyncSessionLocal() as db2:
                review1 = await create_review(db1, profile_id, user_id)
                review2 = await create_review(db2, profile_id, user_id)

                original_agent_orchestration = review_service._run_agent_orchestration
                call_count = {"n": 0}

                async def flaky_agent_orchestration(profile, ingestion_results):
                    call_count["n"] += 1
                    if call_count["n"] == 1:
                        raise RuntimeError("simulated failure in agent orchestration")
                    return await original_agent_orchestration(profile, ingestion_results)

                with patch.object(
                    review_service,
                    "_run_agent_orchestration",
                    side_effect=flaky_agent_orchestration,
                ):
                    try:
                        # Bounded wait: if the lock isn't released on the
                        # exception path, the second review hangs forever
                        # instead of failing cleanly.
                        await asyncio.wait_for(
                            asyncio.gather(
                                process_review(db1, review1.id, profile_id),
                                process_review(db2, review2.id, profile_id),
                            ),
                            timeout=10,
                        )
                    except TimeoutError:
                        pytest.fail(
                            "process_review() calls did not finish within the timeout -- "
                            "the second review likely hung waiting for a lock the first "
                            "never released after raising"
                        )

            async with AsyncSessionLocal() as db:
                r1 = await db.get(Review, review1.id)
                r2 = await db.get(Review, review2.id)

            statuses = {r1.status, r2.status}
            assert statuses == {"failed", "complete"}, (
                f"expected exactly one review to fail and the other to complete, got "
                f"{statuses} (review1={r1.status}, review2={r2.status})"
            )
        finally:
            await self._cleanup(user_id)

    async def test_review_fails_closed_when_lock_cannot_be_acquired(self):
        """If Redis is unreachable, the review must fail closed, not run unprotected.

        Swaps review_service's shared redis_client for one pointed at an
        address nothing is listening on, so lock acquisition raises a real
        redis.exceptions.ConnectionError -- the same error class the outer
        layer in process_review() is built to catch. Verifies both halves of
        the fail-closed decision: the review ends up "failed", and the
        specific profile_lock_acquire_failed event is logged (not just a
        generic error), so an operator can tell a Redis outage apart from an
        actual pipeline bug.
        """
        user_id, profile_id = await self._make_profile()
        try:
            async with AsyncSessionLocal() as db:
                review = await create_review(db, profile_id, user_id)

                broken_client = AsyncRedis.from_url("redis://localhost:1/0")
                try:
                    with (
                        capture_logs() as captured_logs,
                        patch.object(review_service, "redis_client", broken_client),
                    ):
                        await asyncio.wait_for(
                            process_review(db, review.id, profile_id), timeout=10
                        )
                finally:
                    await broken_client.aclose()

            async with AsyncSessionLocal() as db:
                r = await db.get(Review, review.id)
            assert r.status == "failed", (
                f"expected the review to fail closed when the lock couldn't be "
                f"acquired, got '{r.status}'"
            )

            lock_failure_logs = [
                entry for entry in captured_logs
                if entry.get("event") == "profile_lock_acquire_failed"
            ]
            assert len(lock_failure_logs) == 1, (
                f"expected exactly one profile_lock_acquire_failed log entry, got: "
                f"{captured_logs}"
            )
            assert lock_failure_logs[0].get("profile_id") == str(profile_id)
        finally:
            await self._cleanup(user_id)
