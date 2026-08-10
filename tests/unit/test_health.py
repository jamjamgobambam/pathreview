from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_includes_safety_events_last_hour():
    """Health response should include the recent safety event count."""
    mock_db = AsyncMock()
    mock_redis = Mock()

    with (
        patch("redis.Redis.from_url", return_value=mock_redis),
        patch("api.routes.health.SafetyMonitor") as mock_monitor_class,
    ):
        mock_monitor = mock_monitor_class.return_value
        mock_monitor.get_recent_event_count.return_value = 4

        result = await health_check(db=mock_db)

    assert result["safety_events_last_hour"] == 4

    mock_monitor_class.assert_called_once_with(mock_redis)
    mock_monitor.get_recent_event_count.assert_called_once_with(
        window_hours=1
    )