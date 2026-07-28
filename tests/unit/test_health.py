"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock, Mock, patch

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
    def mock_redis_client(self) -> Mock:
        """Create a mock Redis client with a real recorded safety event.

        Simulates what SafetyMonitor.log_event() would have written: a
        pii_detected counter incremented to 5 in Redis.
        """
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)
        redis_client.get = Mock(
            side_effect=lambda key: "5" if key == "safety:events:pii_detected" else None
        )
        return redis_client

    @pytest.fixture
    def mock_settings(self) -> Mock:
        """Fake settings exposing the fields health.py's Redis check reads.

        core/config.py's real Settings only defines `redis_url`, not
        `redis_host`/`redis_port` — health.py references the latter, which
        raises AttributeError and marks Redis unhealthy regardless of this
        test's mocked client. That's a separate latent bug from issue #68;
        this fixture works around it so the test can isolate the
        safety_events_last_hour behavior specifically.
        """
        return Mock(redis_host="localhost", redis_port=6379, vector_db_url="http://localhost:8001")

    @pytest.mark.asyncio
    async def test_safety_events_last_hour_reflects_real_redis_data(
        self, mock_db: AsyncMock, mock_redis_client: Mock, mock_settings: Mock
    ) -> None:
        """safety_events_last_hour should surface real counts, not a hardcoded 0.

        SafetyMonitor already tracks real safety events in Redis
        (safety/monitoring.py), but health.py never calls it and always
        reports 0. This test seeds Redis with a real pii_detected count
        of 5 and asserts the health response reflects it. It currently
        fails, confirming issue #68.
        """
        # health.py does `import redis` / `from core.config import settings`
        # locally inside the function body, so the patch targets are the
        # source modules themselves, not api.routes.health's attributes
        # (which don't exist until those local imports execute).
        with (
            patch("redis.Redis", return_value=mock_redis_client),
            patch("core.config.settings", mock_settings),
        ):
            response = await health_check(db=mock_db)

        assert response["safety_events_last_hour"] != 0
