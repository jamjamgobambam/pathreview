from datetime import datetime
from typing import Annotated, Any

import redis
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
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
    Check health of PostgreSQL, Redis, and Vector DB.
    Returns 200 if all healthy, 503 if any dependency is down.
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "dependencies": {
            "postgres": "unknown",
            "redis": "unknown",
            "vector_db": "unknown",
        },
        "safety_events_last_hour": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        # Check PostgreSQL
        await db.execute(text("SELECT 1"))
        health_status["dependencies"]["postgres"] = "healthy"
        log.debug("postgres_health_check_passed")
    except Exception as exc:
        log.error("postgres_health_check_failed", error=str(exc))
        health_status["dependencies"]["postgres"] = "unhealthy"
        health_status["status"] = "unhealthy"

    redis_client = None

    try:
        # Check Redis
        redis_client = redis.from_url(
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

    try:
        # Check Vector DB
        if settings.vector_db_url:
            health_status["dependencies"]["vector_db"] = "healthy"
            log.debug("vector_db_health_check_passed")
        else:
            health_status["dependencies"]["vector_db"] = "unavailable"
    except Exception as exc:
        log.error("vector_db_health_check_failed", error=str(exc))
        health_status["dependencies"]["vector_db"] = "unhealthy"
        health_status["status"] = "unhealthy"

    try:
        # Count safety events recorded during the last hour
        if redis_client is not None:
            safety_monitor = SafetyMonitor(redis_client)
            health_status["safety_events_last_hour"] = safety_monitor.get_total_event_count(
                window_hours=1
            )

        log.debug(
            "safety_events_check_passed",
            count=health_status["safety_events_last_hour"],
        )
    except Exception as exc:
        log.error("safety_events_check_failed", error=str(exc))

    # Return 503 if any critical dependency is down
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status
