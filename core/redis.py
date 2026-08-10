"""Redis client configuration and FastAPI dependency."""

import redis

from core.config import settings

# Shared, pooled Redis client for the process, built from the configured URL.
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    """Dependency for FastAPI that returns the shared Redis client."""
    return redis_client
