"""Tests for the health endpoint's safety metrics."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_reports_recent_safety_event_count() -> None:
    """The health response should expose the monitor's aggregate count."""
    db = AsyncMock()
    redis_client = Mock()
    redis_client.ping.return_value = True
    settings = SimpleNamespace(
        redis_host="localhost",
        redis_port=6379,
        redis_url="redis://localhost:6379/0",
        vector_db_url="http://localhost:8001",
    )

    with (
        patch("api.routes.health.settings", settings),
        patch(
            "api.routes.health.redis.Redis",
            return_value=redis_client,
        ) as redis_class,
        patch(
            "api.routes.health.SafetyMonitor.get_total_event_count",
            return_value=4,
        ) as get_total,
    ):
        redis_class.from_url.return_value = redis_client
        response = await health_check(db)

    assert response["safety_events_last_hour"] == 4
    redis_class.from_url.assert_called_once_with(
        "redis://localhost:6379/0",
        decode_responses=True,
    )
    get_total.assert_called_once_with(window_hours=1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_keeps_zero_when_safety_count_fails() -> None:
    """A safety monitoring outage should not crash the health endpoint."""
    db = AsyncMock()
    redis_client = Mock()
    redis_client.ping.return_value = True
    settings = SimpleNamespace(
        redis_host="localhost",
        redis_port=6379,
        redis_url="redis://localhost:6379/0",
        vector_db_url="http://localhost:8001",
    )

    with (
        patch("api.routes.health.settings", settings),
        patch(
            "api.routes.health.redis.Redis",
            return_value=redis_client,
        ) as redis_class,
        patch(
            "api.routes.health.SafetyMonitor.get_total_event_count",
            side_effect=RuntimeError("Metrics unavailable"),
        ),
        patch("api.routes.health.log") as logger,
    ):
        redis_class.from_url.return_value = redis_client
        response = await health_check(db)

    assert response["safety_events_last_hour"] == 0
    logger.error.assert_called_with(
        "safety_events_check_failed",
        error="Metrics unavailable",
    )
