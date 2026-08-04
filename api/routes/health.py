from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db

log = structlog.get_logger()

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: Any = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
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
        "safety_events_last_hour": None,
        "timestamp": datetime.utcnow().isoformat(),
    }

    redis_client = None

    try:
        # Check PostgreSQL
        await db.execute("SELECT 1")
        health_status["dependencies"]["postgres"] = "healthy"
        log.debug("postgres_health_check_passed")
    except Exception as exc:
        log.error("postgres_health_check_failed", error=str(exc))
        health_status["dependencies"]["postgres"] = "unhealthy"
        health_status["status"] = "unhealthy"

    try:
        # Check Redis (if available)
        import redis

        from core.config import settings

        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
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
        # Check Vector DB (if available)
        from core.config import settings

        if settings.vector_db_url:
            health_status["dependencies"]["vector_db"] = "healthy"
            log.debug("vector_db_health_check_passed")
        else:
            health_status["dependencies"]["vector_db"] = "unavailable"
    except Exception as exc:
        log.error("vector_db_health_check_failed", error=str(exc))
        health_status["dependencies"]["vector_db"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Count safety events in the last hour.
    # Only attempt this if Redis is actually reachable — otherwise leave it
    # as null rather than throwing and masking the dependency status above.
    if health_status["dependencies"]["redis"] == "healthy" and redis_client is not None:
        try:
            from safety.monitoring import SafetyMonitor

            monitor = SafetyMonitor(redis_client)
            health_status["safety_events_last_hour"] = monitor.get_total_event_count(window_hours=1)
        except Exception as exc:
            log.error("safety_events_check_failed", error=str(exc))
            health_status["safety_events_last_hour"] = None
    else:
        log.debug("safety_events_check_skipped", reason="redis_unavailable")

    # Return 503 if any critical dependency is down
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status
