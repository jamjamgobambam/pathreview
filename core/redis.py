"""Shared Redis client for FastAPI dependency injection."""

import redis

from core.config import settings

_redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    """Dependency for FastAPI that returns the shared Redis client."""
    return _redis_client
