"""Safety event monitoring."""

from datetime import datetime

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

    def get_total_event_count(self, window_hours: int = 1) -> int:
        """Get the total count of safety events across all event types.

        Sums the per-type counts for every value in ``VALID_EVENT_TYPES``. This
        backs the ``safety_events_last_hour`` field on the ``/health`` endpoint so
        operators can see aggregate safety activity in one number.

        Note: the per-type counters are rolling counters with a 24-hour Redis TTL,
        so ``window_hours`` is not strictly enforced here (same limitation already
        documented on ``get_event_count``).

        Args:
            window_hours: Time window in hours (passed through for reference).

        Returns:
            Total number of safety events across all valid event types. Individual
            per-type read failures are already handled by ``get_event_count`` (which
            returns 0), so this method never raises on a Redis error.
        """
        return sum(
            self.get_event_count(event_type, window_hours=window_hours)
            for event_type in self.VALID_EVENT_TYPES
        )
