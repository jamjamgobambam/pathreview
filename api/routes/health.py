"""Health-check API routes."""

from datetime import UTC, datetime
from typing import Annotated, Any

import redis
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from safety.monitoring import SafetyMonitor

log = structlog.get_logger()

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Check the health of PostgreSQL, Redis, and the vector database.

    Returns:
        Health information for the service and its dependencies.

    Raises:
        HTTPException: If a critical dependency is unavailable.
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "dependencies": {
            "postgres": "unknown",
            "redis": "unknown",
            "vector_db": "unknown",
        },
        "safety_events_last_hour": 0,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    redis_client: Redis | None = None

    # PostgreSQL health check
    try:
        await db.execute(text("SELECT 1"))
        health_status["dependencies"]["postgres"] = "healthy"
        log.debug("postgres_health_check_passed")
    except Exception as exc:
        log.error("postgres_health_check_failed", error=str(exc))
        health_status["dependencies"]["postgres"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Redis health check
    try:
        redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        redis_client.ping()

        health_status["dependencies"]["redis"] = "healthy"
        log.debug("redis_health_check_passed")
    except Exception as exc:
        log.error("redis_health_check_failed", error=str(exc))
        health_status["dependencies"]["redis"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Vector database health check
    try:
        if settings.vector_db_url:
            health_status["dependencies"]["vector_db"] = "healthy"
            log.debug("vector_db_health_check_passed")
        else:
            health_status["dependencies"]["vector_db"] = "unavailable"
            log.warning("vector_db_url_not_configured")
    except Exception as exc:
        log.error("vector_db_health_check_failed", error=str(exc))
        health_status["dependencies"]["vector_db"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Count recent safety events
    try:
        if redis_client is not None:
            safety_monitor = SafetyMonitor(redis_client)

            safety_event_count = sum(
                safety_monitor.get_event_count(
                    event_type,
                    window_hours=1,
                )
                for event_type in SafetyMonitor.VALID_EVENT_TYPES
            )

            health_status["safety_events_last_hour"] = safety_event_count
            log.debug(
                "safety_events_check_passed",
                count=safety_event_count,
            )
    except Exception as exc:
        log.error("safety_events_check_failed", error=str(exc))
        health_status["safety_events_last_hour"] = 0

    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status
