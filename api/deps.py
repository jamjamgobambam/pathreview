"""Shared FastAPI dependencies."""

from typing import Annotated

import redis
from fastapi import Depends

from core.redis_client import get_redis
from safety.monitoring import SafetyMonitor


def get_safety_monitor(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> SafetyMonitor:
    """Dependency that provides a SafetyMonitor backed by the shared Redis client."""
    return SafetyMonitor(redis_client)
