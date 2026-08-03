"""Per-profile review lock backed by Redis.

Serializes concurrent review requests for the same profile so overlapping
agent loops cannot read/write the same rows and produce inconsistent output.
See issue #82.
"""

import secrets
from uuid import UUID

import structlog
from redis.asyncio import Redis

log = structlog.get_logger()

# Compare-and-delete: only release the lock if we still own the token.
# Prevents a stale owner (whose TTL fired) from deleting a fresh holder's lock.
_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class ReviewLock:
    """Redis-backed per-profile mutex.

    Uses SET NX EX for atomic acquire and a token + Lua compare-and-delete
    on release. TTL bounds the blast radius of a crashed holder.
    """

    def __init__(
        self,
        redis_client: Redis,
        profile_id: UUID,
        ttl_seconds: int = 300,
    ) -> None:
        self._redis = redis_client
        self._key = f"review_lock:{profile_id}"
        self._ttl_seconds = ttl_seconds
        self._token = secrets.token_hex(16)

    @property
    def key(self) -> str:
        return self._key

    async def acquire(self) -> bool:
        """Attempt to acquire the lock. Returns True on success."""
        acquired = await self._redis.set(self._key, self._token, nx=True, ex=self._ttl_seconds)
        return bool(acquired)

    async def release(self) -> None:
        """Release the lock if we still own it. Silent on foreign locks."""
        try:
            await self._redis.eval(_RELEASE_LUA, 1, self._key, self._token)
        except Exception as exc:
            log.error("review_lock_release_failed", key=self._key, error=str(exc))
