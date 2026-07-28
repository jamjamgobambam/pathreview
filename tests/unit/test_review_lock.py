"""Tests for the per-profile review lock (issue #82)."""

from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from core.services.review_lock import ReviewLock


@pytest.mark.unit
class TestReviewLock:
    """Tests for ReviewLock's acquire/release semantics against a fake Redis."""

    @pytest.mark.asyncio
    async def test_acquire_uses_set_nx_ex_on_profile_key(self) -> None:
        profile_id = uuid4()
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)

        lock = ReviewLock(redis, profile_id, ttl_seconds=300)
        acquired = await lock.acquire()

        assert acquired is True
        redis.set.assert_awaited_once()
        args, kwargs = redis.set.call_args
        assert args[0] == f"review_lock:{profile_id}"
        assert kwargs["nx"] is True
        assert kwargs["ex"] == 300

    @pytest.mark.asyncio
    async def test_acquire_returns_false_when_key_exists(self) -> None:
        """redis-py returns None when SET NX loses the race."""
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=None)

        lock = ReviewLock(redis, uuid4())
        assert await lock.acquire() is False

    @pytest.mark.asyncio
    async def test_ttl_defaults_to_five_minutes(self) -> None:
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)

        lock = ReviewLock(redis, uuid4())
        await lock.acquire()

        _, kwargs = redis.set.call_args
        assert kwargs["ex"] == 300

    @pytest.mark.asyncio
    async def test_concurrent_acquire_only_one_wins(self) -> None:
        """Two ReviewLocks contending on one profile: exactly one gets True."""
        profile_id = uuid4()

        class FakeRedis:
            def __init__(self) -> None:
                self._store: dict[str, str] = {}
                self.set = AsyncMock(side_effect=self._set)
                self.eval = AsyncMock(side_effect=self._eval)

            async def _set(
                self, key: str, value: str, nx: bool = False, ex: int | None = None
            ) -> bool | None:
                if nx and key in self._store:
                    return None
                self._store[key] = value
                return True

            async def _eval(self, _script: str, _numkeys: int, key: str, token: str) -> int:
                if self._store.get(key) == token:
                    del self._store[key]
                    return 1
                return 0

        redis: Any = FakeRedis()
        first = ReviewLock(cast(Redis, redis), profile_id)
        second = ReviewLock(cast(Redis, redis), profile_id)

        assert await first.acquire() is True
        assert await second.acquire() is False

        # After the winner releases, another acquirer can take the lock.
        await first.release()
        third = ReviewLock(cast(Redis, redis), profile_id)
        assert await third.acquire() is True

    @pytest.mark.asyncio
    async def test_release_uses_compare_and_delete_lua(self) -> None:
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)
        redis.eval = AsyncMock(return_value=1)

        lock = ReviewLock(redis, uuid4())
        await lock.acquire()
        await lock.release()

        redis.eval.assert_awaited_once()
        args, _ = redis.eval.call_args
        script, numkeys, key, token = args
        assert "redis.call" in script
        assert numkeys == 1
        assert key == lock.key
        # Token is generated in __init__ and passed as ARGV[1].
        assert isinstance(token, str) and len(token) > 0

    @pytest.mark.asyncio
    async def test_release_swallows_redis_errors(self) -> None:
        """Background-task teardown must not crash if Redis is unavailable."""
        redis = AsyncMock()
        redis.eval = AsyncMock(side_effect=RuntimeError("redis down"))
        lock = ReviewLock(redis, uuid4())
        # Should not propagate.
        await lock.release()

    @pytest.mark.asyncio
    async def test_release_does_not_delete_foreign_lock(self) -> None:
        """
        If our TTL fires and someone else acquires the same key, our release
        must not delete their key. The Lua script does GET==token ? DEL : 0
        on the server side; here we assert the eval returns 0 (no delete)
        when the token doesn't match.
        """

        class FakeRedis:
            def __init__(self) -> None:
                # Simulate a foreign owner already holding the key with a
                # different token.
                self._store: dict[str, str] = {}
                self.set = AsyncMock(side_effect=self._set)
                self.eval = AsyncMock(side_effect=self._eval)

            async def _set(
                self, key: str, value: str, nx: bool = False, ex: int | None = None
            ) -> bool | None:
                if nx and key in self._store:
                    return None
                self._store[key] = value
                return True

            async def _eval(self, _script: str, _numkeys: int, key: str, token: str) -> int:
                if self._store.get(key) == token:
                    del self._store[key]
                    return 1
                return 0

        redis: Any = FakeRedis()
        lock = ReviewLock(cast(Redis, redis), uuid4())
        # Foreign owner takes the key with a different token.
        redis._store[lock.key] = "someone-elses-token"

        await lock.release()

        # Foreign owner's key still there — we did not delete it.
        assert redis._store.get(lock.key) == "someone-elses-token"
