"""
Reproduction + fix verification for issue #82: Concurrent review requests
for the same profile can produce inconsistent results.

Root cause: neither create_review() nor _run_ingestion_pipeline() in
core/services/review_service.py checked for an existing in-flight review
before proceeding, so two calls for the same profile_id always produced
two independent Review rows.

Fix: create_review() now relies on a DB-level partial unique index
(one row per profile_id with status in ("pending", "processing")) and
raises ReviewAlreadyInProgressError when the second concurrent insert
violates it.

_FakeReviewsTable simulates the shared Postgres table + partial unique
index; FakeAsyncSession simulates one DB session/connection. Concurrent
requests in production each get their own session (via Depends(get_db))
but write to the same table -- so each concurrency test below gives each
"request" its own FakeAsyncSession instance, all pointed at one shared
_FakeReviewsTable, rather than sharing a single session object. See
tests/integration/ for the real-DB version of this same scenario.
"""

import asyncio
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from core.models.review import Review
from core.services.review_service import (
    ACTIVE_REVIEW_STATUSES,
    ReviewAlreadyInProgressError,
    create_review,
)


class _FakeScalars:
    def __init__(self, results: list[object]) -> None:
        self._results = results

    def first(self) -> object | None:
        return self._results[0] if self._results else None

    def all(self) -> list[object]:
        return list(self._results)


class _FakeResult:
    def __init__(self, results: list[object]) -> None:
        self._results = results

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._results)


class _FakeReviewsTable:
    """
    Shared table state, simulating the real `reviews` table plus its
    partial unique index (uq_reviews_profile_active). Independent of
    any one session -- multiple FakeAsyncSession instances can point
    at the same table, just like multiple real DB connections hitting
    the same Postgres table.
    """

    def __init__(self) -> None:
        self.rows_by_id: dict[UUID, Review] = {}

    def commit_review(self, review: Review) -> None:
        """Raise IntegrityError if this would violate the partial unique index."""
        if review.status in ACTIVE_REVIEW_STATUSES:
            for other in self.rows_by_id.values():
                if (
                    other.id != review.id
                    and other.profile_id == review.profile_id
                    and other.status in ACTIVE_REVIEW_STATUSES
                ):
                    raise IntegrityError(
                        "mock unique violation on (profile_id) WHERE status "
                        "IN ('pending', 'processing')",
                        params={},
                        orig=Exception("uq_reviews_profile_active"),
                    )
        self.rows_by_id[review.id] = review

    def active_reviews_for_profile(self, profile_id: UUID) -> list[Review]:
        return [
            r
            for r in self.rows_by_id.values()
            if r.profile_id == profile_id and r.status in ACTIVE_REVIEW_STATUSES
        ]


class FakeAsyncSession:
    """
    Minimal stand-in for one real async DB session/connection. Holds its
    own pending (not-yet-committed) objects; commit() checks them against
    the shared _FakeReviewsTable, same as a real transaction would check
    against the real unique index at commit time.
    """

    def __init__(self, table: _FakeReviewsTable) -> None:
        self.table = table
        self._pending: list[object] = []

    def add(self, obj: object) -> None:
        self._pending.append(obj)

    async def commit(self) -> None:
        # Yield control, same as a real DB round-trip would -- this is
        # what lets asyncio.gather() genuinely interleave concurrent
        # calls rather than running them back-to-back with no gap.
        await asyncio.sleep(0.01)

        for obj in self._pending:
            if isinstance(obj, Review):
                if getattr(obj, "id", None) is None:
                    obj.id = uuid4()  # type: ignore[attr-defined]
                self.table.commit_review(obj)

        self._pending = []

    async def rollback(self) -> None:
        self._pending = []

    async def refresh(self, obj: object) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()  # type: ignore[attr-defined]

    async def execute(self, stmt: object) -> _FakeResult:
        # Simplification: doesn't parse `stmt` -- returns every active
        # review in the table regardless of the WHERE clause's profile_id.
        # Fine here because execute() is only reached via create_review's
        # IntegrityError branch, and every test below has at most one
        # profile with an active review at the point execute() runs.
        return _FakeResult(list(self.table.rows_by_id.values()))


@pytest.mark.unit
class TestConcurrentReviewRace:
    """Fix verification tests for issue #82."""

    @pytest.mark.asyncio
    async def test_concurrent_create_review_same_profile_rejects_second(self) -> None:
        """
        Two concurrent create_review() calls for the SAME profile_id,
        each on its own session (as separate requests would be), should
        produce exactly one pending Review; the other should be rejected
        with ReviewAlreadyInProgressError pointing at the one that succeeded.
        """
        profile_id = uuid4()
        user_id = uuid4()
        table = _FakeReviewsTable()
        db_a = FakeAsyncSession(table)
        db_b = FakeAsyncSession(table)

        results = await asyncio.gather(
            create_review(db_a, profile_id, user_id),
            create_review(db_b, profile_id, user_id),
            return_exceptions=True,
        )

        successes = [r for r in results if isinstance(r, Review)]
        rejections = [r for r in results if isinstance(r, ReviewAlreadyInProgressError)]

        assert len(successes) == 1, (
            f"expected exactly 1 successful Review for a shared profile_id, "
            f"got {len(successes)}"
        )
        assert (
            len(rejections) == 1
        ), f"expected exactly 1 ReviewAlreadyInProgressError, got {len(rejections)}"
        assert rejections[0].existing_review.id == successes[0].id

    @pytest.mark.asyncio
    async def test_concurrent_create_review_different_profiles_both_succeed(
        self,
    ) -> None:
        """
        The guard is scoped per profile_id -- concurrent requests for
        two different profiles, on separate sessions, must not block
        each other.
        """
        user_id = uuid4()
        table = _FakeReviewsTable()
        db_a = FakeAsyncSession(table)
        db_b = FakeAsyncSession(table)

        review_a, review_b = await asyncio.gather(
            create_review(db_a, uuid4(), user_id),
            create_review(db_b, uuid4(), user_id),
        )

        assert review_a.id != review_b.id
        assert review_a.profile_id != review_b.profile_id

    @pytest.mark.asyncio
    async def test_create_review_allowed_once_previous_review_leaves_active_state(
        self,
    ) -> None:
        """
        Once an existing review for a profile moves out of the active
        set (e.g. process_review marks it "failed" or "complete"), a
        new create_review() call for that profile should succeed again
        -- the guard must not permanently lock out a profile. Sequential,
        not concurrent, so a single shared session is fine here.
        """
        profile_id = uuid4()
        user_id = uuid4()
        table = _FakeReviewsTable()
        db = FakeAsyncSession(table)

        first = await create_review(db, profile_id, user_id)

        # Simulate process_review() finishing (successfully or via its
        # existing except-block on crash) and flipping status.
        first.status = "complete"
        db.add(first)
        await db.commit()

        second = await create_review(db, profile_id, user_id)

        assert second.id != first.id


# NOTE: a reproduction test targeting _run_ingestion_pipeline()
# duplication was attempted here, but it's currently blocked by an
# unrelated bug: _run_ingestion_pipeline() constructs
# IngestedSource(..., raw_data=json.dumps(github_data)), but the real
# IngestedSource model (core/models/ingested_source.py) has no
# `raw_data` column -- only source_type, source_url, filename,
# content_hash, chunk_count. That TypeError is caught internally and
# only logged ("github_ingestion_failed"), so ingestion silently
# produces zero rows on every call right now, concurrent or not.
# This is a separate, more severe defect than #82 and is out of this
# issue's scope -- flagging it for a mentor/TA rather than fixing it
# here. See JOURNAL.md Week 8 blockers.
