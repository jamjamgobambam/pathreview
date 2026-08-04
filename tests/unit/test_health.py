"""Tests for the health_check route in api/routes/health.py.

These focus on the ``safety_events_last_hour`` portion of the health response.
The route depends on FastAPI's ``get_db`` dependency, which we override with a
mock async session (following the dependency-override pattern used elsewhere),
and it lazily imports ``redis`` / ``SafetyMonitor`` / ``settings`` inside the
handler, which we patch with ``unittest.mock``.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.database import get_db
from safety.monitoring import SafetyMonitor

# The real set of event types the route sums over.
VALID_EVENT_TYPES = SafetyMonitor.VALID_EVENT_TYPES


def _settings_mock():
    """A settings stand-in exposing the attributes the health route reads.

    The route builds ``redis.Redis(host=settings.redis_host, port=...)`` and
    checks ``settings.vector_db_url``; those attribute lookups happen before the
    (patched) ``redis.Redis`` is called, so they must resolve.
    """
    settings = Mock()
    settings.redis_host = "localhost"
    settings.redis_port = 6379
    settings.vector_db_url = "http://localhost:8001"
    return settings


@pytest.fixture
def client():
    """TestClient with ``get_db`` overridden to yield a healthy mock session.

    The client is created without the ``with`` context manager so app startup
    (which would try to connect to Postgres) does not run.
    """

    async def override_get_db():
        session = AsyncMock()
        # ``await db.execute("SELECT 1")`` should succeed -> postgres healthy.
        session.execute = AsyncMock(return_value=None)
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.unit
class TestHealthCheckSafetyEvents:
    """Tests for the ``safety_events_last_hour`` field of the health check."""

    def test_safety_events_equals_sum_across_all_event_types(self, client):
        """safety_events_last_hour is the sum of per-type counts over VALID_EVENT_TYPES."""
        counts = {
            "pii_detected": 5,
            "injection_attempt": 3,
            "content_filtered": 2,
            "bias_detected": 1,
            "rate_limited": 4,
        }
        # Guard against the route's event-type set drifting from this test.
        assert set(counts) == set(VALID_EVENT_TYPES)
        expected_total = sum(counts.values())

        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)

        with (
            patch("redis.Redis", return_value=redis_client),
            patch("core.config.settings", _settings_mock()),
            patch("safety.monitoring.SafetyMonitor") as mock_monitor_class,
        ):
            mock_monitor_class.VALID_EVENT_TYPES = VALID_EVENT_TYPES
            mock_monitor_class.return_value.get_event_count.side_effect = (
                lambda event_type, window_hours=1: counts[event_type]
            )

            response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["safety_events_last_hour"] == expected_total
        # One count per event type, each over the 1-hour window.
        monitor = mock_monitor_class.return_value
        assert monitor.get_event_count.call_count == len(VALID_EVENT_TYPES)
        for call in monitor.get_event_count.call_args_list:
            assert call.kwargs.get("window_hours") == 1

    def test_safety_events_falls_back_to_zero_when_monitor_raises(self, client):
        """If SafetyMonitor raises, the field degrades to 0 and the check still responds."""
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)

        with (
            patch("redis.Redis", return_value=redis_client),
            patch("core.config.settings", _settings_mock()),
            patch("safety.monitoring.SafetyMonitor") as mock_monitor_class,
        ):
            mock_monitor_class.VALID_EVENT_TYPES = VALID_EVENT_TYPES
            mock_monitor_class.return_value.get_event_count.side_effect = RuntimeError(
                "monitor exploded"
            )

            response = client.get("/health")

        # Postgres and Redis are healthy, so the overall check is still 200 and
        # did not crash despite the safety subsystem blowing up.
        assert response.status_code == 200
        assert response.json()["safety_events_last_hour"] == 0

    def test_safety_events_falls_back_to_zero_when_redis_unavailable(self, client):
        """If Redis ping fails, safety_events_last_hour degrades to 0 rather than raising."""
        # redis.Redis(...) constructs fine, but ping() fails -> Redis dep unhealthy.
        redis_client = Mock()
        redis_client.ping = Mock(side_effect=ConnectionError("redis down"))

        with (
            patch("redis.Redis", return_value=redis_client),
            patch("core.config.settings", _settings_mock()),
            patch("safety.monitoring.SafetyMonitor") as mock_monitor_class,
        ):
            mock_monitor_class.VALID_EVENT_TYPES = VALID_EVENT_TYPES
            # With Redis down, the monitor's backing calls fail too.
            mock_monitor_class.return_value.get_event_count.side_effect = ConnectionError(
                "redis down"
            )

            response = client.get("/health")

        # A down Redis makes the overall status 503, but the endpoint still
        # returns a structured payload with safety_events_last_hour degraded to 0
        # instead of propagating an unhandled error.
        assert response.status_code == 503
        payload = response.json()["detail"]
        assert payload["dependencies"]["redis"] == "unhealthy"
        assert payload["safety_events_last_hour"] == 0
