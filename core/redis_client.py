"""Async Redis client for cross-process coordination (e.g. per-profile locks).

Separate from the synchronous redis.Redis client used elsewhere in this
codebase (safety/rate_limiter.py, agent/memory/session_store.py,
api/routes/health.py) -- those make quick, occasional calls where blocking
briefly is fine. A lock held for the duration of a review's processing needs
the async client so it doesn't block the single-threaded event loop while
waiting on acquisition.
"""

from redis.asyncio import Redis

from core.config import settings

redis_client = Redis.from_url(settings.redis_url)
