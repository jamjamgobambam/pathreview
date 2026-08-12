"""Safety event monitoring."""

import time

import redis
import structlog

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events."""

    # Valid event types
    VALID_EVENT_TYPES = {
        "pii_detected",
        "injection_attempt",
        "content_filtered",
        "bias_detected",
        "rate_limited",
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

        now = time.time()

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Record event in a rolling window sorted set, scored by timestamp
            key = f"safety:events:{event_type}"
            self.redis.zadd(key, {str(now): now})
            # Set expiry comfortably above the largest window we query
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: float = 1) -> int:
        """Get count of safety events within a rolling time window.

        Args:
            event_type: Type of event
            window_hours: Time window in hours

        Returns:
            Count of events in the window
        """
        key = f"safety:events:{event_type}"
        now = time.time()
        window_start = now - (window_hours * 3600)

        try:
            # Evict entries that have fallen outside the window
            self.redis.zremrangebyscore(key, 0, window_start)
            return self.redis.zcount(key, window_start, now)

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: float = 1) -> int:
        """Get total count of safety events across all event types.

        Args:
            window_hours: Time window in hours

        Returns:
            Sum of event counts across all VALID_EVENT_TYPES in the window
        """
        return sum(
            self.get_event_count(event_type, window_hours=window_hours)
            for event_type in self.VALID_EVENT_TYPES
        )
