"""Safety event monitoring."""

import redis
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events."""

    # Valid event types
    VALID_EVENT_TYPES = {
        "pii_detected",
        "injection_attempt",
        "content_filtered",
        "bias_detected",
        "rate_limited"
    }

    def __init__(self, redis_client: redis.Redis):
        """Initialize safety monitor.

        Args:
            redis_client: Redis client
        """
        self.redis = redis_client

    def log_event(self, event_type: str, details: dict) -> None:
        """Log a safety event.

        Args:
            event_type: Type of event (from VALID_EVENT_TYPES)
            details: Event details dict
        """
        if event_type not in self.VALID_EVENT_TYPES:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        timestamp = datetime.utcnow().isoformat()

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Store count in Redis for monitoring
            key = f"safety:events:{event_type}"
            self.redis.incr(key)
            # Set expiry to 24 hours
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events.

        Args:
            event_type: Type of event
            window_hours: Time window in hours (not enforced here; for reference)

        Returns:
            Count of events in the window
        """
        key = f"safety:events:{event_type}"

        try:
            count = self.redis.get(key)
            return int(count) if count else 0

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0
