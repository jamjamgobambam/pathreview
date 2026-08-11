"""Safety event monitoring."""

import time
import uuid

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

        try:
            # Log to structlog
            logger.warning("safety_event", event_type=event_type, **details)

            # Record event in a Redis sorted set (score = timestamp) so counts
            # can be read back over an arbitrary rolling window.
            key = f"safety:events:{event_type}"
            now = time.time()
            self.redis.zadd(key, {f"{now}:{uuid.uuid4()}": now})
            # Set expiry to 24 hours
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events in a rolling time window.

        Args:
            event_type: Type of event
            window_hours: Time window in hours

        Returns:
            Count of events within the last `window_hours` hours
        """
        key = f"safety:events:{event_type}"
        window_start = time.time() - (window_hours * 3600)

        try:
            # Prune entries outside the window, then count what remains
            self.redis.zremrangebyscore(key, 0, window_start)
            return self.redis.zcard(key)

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Get the total count of safety events across all event types.

        Args:
            window_hours: Time window in hours

        Returns:
            Sum of event counts across all VALID_EVENT_TYPES within the window
        """
        return sum(
            self.get_event_count(event_type, window_hours=window_hours)
            for event_type in self.VALID_EVENT_TYPES
        )
