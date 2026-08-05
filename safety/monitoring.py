"""Safety event monitoring."""

import time

import redis
import structlog

logger = structlog.get_logger()


class SafetyMonitor:
    """Monitor and log safety events."""

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
            logger.warning("safety_event", event_type=event_type, **details)

            key = f"safety:events:{event_type}:zset"
            now = time.time()
            # Score = timestamp, member must be unique per event
            self.redis.zadd(key, {f"{now}:{id(details)}": now})
            # Keep the key from growing forever even if nobody reads it
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events within a real rolling window.

        Args:
            event_type: Type of event
            window_hours: Time window in hours, enforced via ZREMRANGEBYSCORE

        Returns:
            Count of events in the window
        """
        key = f"safety:events:{event_type}:zset"
        cutoff = time.time() - (window_hours * 3600)

        try:
            # Prune anything older than the window, then count what's left
            self.redis.zremrangebyscore(key, 0, cutoff)
            return self.redis.zcard(key)

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Get total count of safety events across all event types.

        Args:
            window_hours: Time window in hours

        Returns:
            Summed count across all VALID_EVENT_TYPES
        """
        total = 0
        for event_type in self.VALID_EVENT_TYPES:
            total += self.get_event_count(event_type, window_hours)
        return total
