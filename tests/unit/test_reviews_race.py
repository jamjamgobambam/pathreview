"""Regression test for issue #82: concurrent reviews for the same profile.

Two concurrent `POST /reviews` for the same profile must not both succeed.
The second overlapping request must be rejected with HTTPException(400)
while the first is still in flight.

This test FAILS against `main` today (both concurrent calls succeed) and
turns green once the per-profile Redis lock is wired into the endpoint.
"""

import asyncio
import inspect
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


class _InProcessRedis:
    """Minimal async fake honoring SET NX EX + EVAL compare-and-delete.

    Shared across the two concurrent endpoint invocations so they contend
    for the same profile lock key the way real Redis would.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(
        self, key: str, value: str, nx: bool = False, ex: int | None = None
    ) -> bool | None:
        if nx and key in self._store:
            return None
        self._store[key] = value
        return True

    async def eval(self, _script: str, _numkeys: int, key: str, token: str) -> int:
        if self._store.get(key) == token:
            del self._store[key]
            return 1
        return 0


def _endpoint_accepts_redis() -> bool:
    """True once the fix wires a `redis` dependency into the endpoint."""
    return "redis" in inspect.signature(create_review_endpoint).parameters


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_creates_for_same_profile_reject_second() -> None:
    """
    Fires two concurrent create_review_endpoint calls for the same profile
    and asserts exactly one succeeds while the other raises
    HTTPException(status_code=400).
    """
    profile_id = uuid4()
    user = Mock()
    user.id = uuid4()
    redis = _InProcessRedis()

    async def one_call() -> tuple[str, Any]:
        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        bg = BackgroundTasks()

        fake_review = Mock()
        fake_review.id = uuid4()
        fake_review.profile_id = profile_id
        fake_review.status = "pending"
        fake_review.sections = None
        fake_review.overall_score = None
        fake_review.created_at = None
        fake_review.updated_at = None

        kwargs: dict[str, Any] = dict(
            data=ReviewCreate(profile_id=profile_id),
            background_tasks=bg,
            current_user=user,
            db=db,
        )
        if _endpoint_accepts_redis():
            kwargs["redis"] = redis

        with (
            patch(
                "api.routes.reviews.create_review",
                AsyncMock(return_value=fake_review),
            ),
            patch(
                "api.routes.reviews.ReviewResponse.model_validate",
                return_value=fake_review,
            ),
        ):
            try:
                await create_review_endpoint(**kwargs)
            except HTTPException as exc:
                return ("err", exc.status_code)
            return ("ok", None)

    outcomes = await asyncio.gather(one_call(), one_call())

    ok_count = sum(1 for tag, _ in outcomes if tag == "ok")
    rejects = [code for tag, code in outcomes if tag == "err"]

    assert ok_count == 1, (
        f"Regression #82: expected exactly one success across two concurrent "
        f"POST /reviews for the same profile, got outcomes={outcomes}"
    )
    assert rejects == [400], (
        f"Regression #82: expected the second concurrent request to be "
        f"rejected with HTTP 400, got rejects={rejects}"
    )
