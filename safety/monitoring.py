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

        Each event is stored as a timestamped member in a Redis sorted set so
        that counts can be computed over a rolling time window (mirroring
        ``RateLimiter``). This lets multi-turn conversations that trip the
        content filter across several turns be counted within a window.

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

            # Store a timestamped entry in a sorted set for windowed counting.
            key = f"safety:events:{event_type}"
            now = time.time()
            self.redis.zadd(key, {str(now): now})
            # Expiry covers the largest window we query; the set self-trims.
            self.redis.expire(key, 86400)

        except Exception as e:
            logger.error("safety_monitor_error", error=str(e))

    def get_event_count(self, event_type: str, window_hours: int = 1) -> int:
        """Get count of safety events within a rolling window.

        Args:
            event_type: Type of event
            window_hours: Rolling time window in hours

        Returns:
            Count of events recorded within the last ``window_hours`` hours.
        """
        key = f"safety:events:{event_type}"
        now = time.time()
        window_start = now - window_hours * 3600

        try:
            # Drop events older than the window, then count what remains.
            self.redis.zremrangebyscore(key, 0, window_start)
            return self.redis.zcard(key)

        except Exception as e:
            logger.error("event_count_error", event_type=event_type, error=str(e))
            return 0
