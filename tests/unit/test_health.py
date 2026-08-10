"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock

import pytest

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint's safety event count."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock async DB session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_redis_client_with_events(self) -> Mock:
        """Create a mock Redis client with real recorded safety events.

        Simulates what SafetyMonitor.log_event() would have written:
        - pii_detected: 5
        - injection_attempt: 2
        - content_filtered: 1
        - bias_detected: 0 (no count key, returns None)
        - rate_limited: 0 (no count key, returns None)
        Total expected: 8
        """
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)

        def get_side_effect(key: str) -> str | None:
            event_counts = {
                "safety:events:pii_detected": "5",
                "safety:events:injection_attempt": "2",
                "safety:events:content_filtered": "1",
                "safety:events:bias_detected": None,
                "safety:events:rate_limited": None,
            }
            return event_counts.get(key)

        redis_client.get = Mock(side_effect=get_side_effect)
        return redis_client

    @pytest.fixture
    def mock_redis_client_no_events(self) -> Mock:
        """Create a mock Redis client with no safety events recorded."""
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)
        redis_client.get = Mock(return_value=None)
        return redis_client

    @pytest.mark.asyncio
    async def test_safety_events_last_hour_reflects_real_redis_data(
        self, mock_db: AsyncMock, mock_redis_client_with_events: Mock
    ) -> None:
        """safety_events_last_hour should surface real counts, not a hardcoded 0.

        SafetyMonitor already tracks real safety events in Redis
        (safety/monitoring.py), but health.py never called it and always
        reported 0. This test seeds Redis with real event counts and
        asserts the health response reflects them.
        """
        response = await health_check(db=mock_db, redis_client=mock_redis_client_with_events)

        # Should sum counts across all event types: 5 + 2 + 1 + 0 + 0 = 8
        assert response["safety_events_last_hour"] == 8
        assert response["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_safety_events_last_hour_zero_when_no_events(
        self, mock_db: AsyncMock, mock_redis_client_no_events: Mock
    ) -> None:
        """safety_events_last_hour should be 0 when no events have been recorded."""
        response = await health_check(db=mock_db, redis_client=mock_redis_client_no_events)

        assert response["safety_events_last_hour"] == 0
        assert response["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_safety_events_check_handles_redis_error_gracefully(
        self, mock_db: AsyncMock
    ) -> None:
        """safety_events_check should not crash if Redis errors occur.

        If SafetyMonitor encounters an error while reading counts, the
        health check should log it and keep going (don't mark as unhealthy).
        """
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)
        # Simulate error when getting event count
        redis_client.get = Mock(side_effect=Exception("Redis connection lost"))

        response = await health_check(db=mock_db, redis_client=redis_client)

        # Safety event count should remain at initial 0 on error
        # (health check logs the error but continues)
        assert response["safety_events_last_hour"] == 0
        # The overall health status should still be healthy because
        # safety events are informational, not critical
        assert response["status"] == "healthy"
