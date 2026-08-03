"""Async Redis client provider."""

from functools import lru_cache

from redis.asyncio import Redis

from core.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    """Return a process-wide async Redis client.

    Cached so route dependencies reuse a single connection pool.
    """
    return Redis.from_url(settings.redis_url, decode_responses=True)
