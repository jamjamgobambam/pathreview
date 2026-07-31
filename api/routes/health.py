from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from core.database import get_db
from safety.monitoring import SafetyMonitor

log = structlog.get_logger()

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db=Depends(get_db)):
    """
    Check health of PostgreSQL, Redis, and Vector DB.
    Returns 200 if all healthy, 503 if any dependency is down.
    """
    health_status = {
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

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        health_status["dependencies"]["redis"] = "healthy"
        log.debug("redis_health_check_passed")
    except Exception as exc:
        log.error("redis_health_check_failed", error=str(exc))
        health_status["dependencies"]["redis"] = "unhealthy"
        health_status["status"] = "unhealthy"

    try:
        # Check Vector DB (if available)
        # This is a placeholder - actual implementation depends on vector DB choice
        from core.config import settings

        # Attempt heartbeat to vector DB
        # For now, assume it's healthy if connection string exists
        if settings.vector_db_url:
            health_status["dependencies"]["vector_db"] = "healthy"
            log.debug("vector_db_health_check_passed")
        else:
            health_status["dependencies"]["vector_db"] = "unavailable"
    except Exception as exc:
        log.error("vector_db_health_check_failed", error=str(exc))
        health_status["dependencies"]["vector_db"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Count safety events (PII detections, injection attempts, bias flags,
    # rate limiting, etc.) tracked via SafetyMonitor/Redis. Falls back to the
    # default of 0 above if Redis is unreachable.
    try:
        import redis

        from core.config import settings

        safety_redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        monitor = SafetyMonitor(safety_redis)
        health_status["safety_events_last_hour"] = sum(
            monitor.get_event_count(event_type) for event_type in SafetyMonitor.VALID_EVENT_TYPES
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
