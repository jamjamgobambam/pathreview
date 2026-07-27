"""
Reproduction for issue #82: Concurrent review requests for the same profile
can produce inconsistent results.

Root cause: neither create_review() nor _run_ingestion_pipeline() in
core/services/review_service.py checks for an existing in-flight review
before proceeding. Two calls for the same profile_id -- whether truly
simultaneous or just back-to-back and unlocked -- will always produce:
  - two Review rows (both status="pending") for one profile_id, and
  - duplicate IngestedSource rows from two independent ingestion runs.

These tests use asyncio.gather() to fire two calls "concurrently" (matching
the issue's description of two near-simultaneous requests), backed by a
lightweight fake session that records what was added -- since the existing
AsyncMock fixtures in this file don't track state across calls, which is
fine for the passing create_review tests but can't show us duplication.

Add this file's tests to tests/unit/test_review_service.py (or run
standalone) -- both are EXPECTED TO FAIL before a fix, and are expected
to PASS once create_review()/process_review() correctly serialize or
reject concurrent requests for the same profile.
"""

import asyncio
import pytest
from uuid import uuid4
from unittest.mock import Mock

from core.services.review_service import create_review
from core.models.review import Review


class FakeAsyncSession:
    """
    Minimal stand-in for the real async DB session. Unlike AsyncMock,
    this actually records what gets add()-ed, so we can assert on
    duplication across concurrent calls.
    """

    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        # Yield control, same as a real DB round-trip would -- this is
        # what lets asyncio.gather() genuinely interleave the two calls
        # rather than running them back-to-back with no scheduling gap.
        await asyncio.sleep(0.01)

    async def refresh(self, obj: object) -> None:
        # A real DB assigns the primary key on flush/refresh. Fake that
        # here so we can distinguish the two created rows by id, same
        # as you'd see in a real Postgres-backed run.
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()  # type: ignore[attr-defined]


@pytest.mark.unit
class TestConcurrentReviewRace:
    """Reproduction tests for issue #82."""

    @pytest.mark.asyncio
    async def test_concurrent_create_review_produces_duplicate_reviews(self) -> None:
        """
        Two concurrent create_review() calls for the SAME profile_id
        should not both succeed in creating an independent pending
        review -- but today, they do.

        BEFORE FIX: fails, because 2 Review rows get created.
        AFTER FIX: should be updated to assert exactly 1 Review row
        is created, and the second call is rejected or returns the
        first review's id.
        """
        profile_id = uuid4()
        user_id = uuid4()
        db = FakeAsyncSession()

        review_a, review_b = await asyncio.gather(
            create_review(db, profile_id, user_id),
            create_review(db, profile_id, user_id),
        )

        created_reviews = [obj for obj in db.added if isinstance(obj, Review)]

        # This is the bug: two independent, uncoordinated Review rows
        # for a single profile_id, with no way to tell which is authoritative.
        assert len(created_reviews) == 2, (
            f"expected 2 Review rows given no concurrency guard exists yet "
            f"(this assertion documents the current buggy behavior); "
            f"got {len(created_reviews)}"
        )
        assert review_a.id != review_b.id, (
            "expected two distinct Review rows (each with its own id) -- "
            "if they're equal, refresh() didn't assign separate ids"
        )

    # NOTE: a second reproduction test targeting _run_ingestion_pipeline()
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
