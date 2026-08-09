"""Tests for the health-check endpoint."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check
from safety.monitoring import SafetyMonitor


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_reports_total_safety_events() -> None:
    """Return the total safety events recorded during the previous hour."""
    mock_db = AsyncMock()
    mock_redis_client = Mock()
    mock_redis_client.ping.return_value = True

    event_counts = {
        event_type: index + 1 for index, event_type in enumerate(SafetyMonitor.VALID_EVENT_TYPES)
    }

    with (
        patch(
            "api.routes.health.redis.Redis.from_url",
            return_value=mock_redis_client,
        ),
        patch(
            "api.routes.health.SafetyMonitor.get_event_count",
            side_effect=lambda event_type, window_hours: event_counts[event_type],
        ) as mock_get_event_count,
    ):
        response = await health_check(mock_db)

    assert response["status"] == "healthy"
    assert response["dependencies"]["postgres"] == "healthy"
    assert response["dependencies"]["redis"] == "healthy"
    assert response["safety_events_last_hour"] == sum(event_counts.values())

    mock_db.execute.assert_awaited_once()
    mock_redis_client.ping.assert_called_once()
    assert mock_get_event_count.call_count == len(SafetyMonitor.VALID_EVENT_TYPES)

    for event_type in SafetyMonitor.VALID_EVENT_TYPES:
        mock_get_event_count.assert_any_call(
            event_type,
            window_hours=1,
        )
