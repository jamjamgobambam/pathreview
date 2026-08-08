"""Tests for issue #68: safety_events_last_hour on the /health endpoint.

`health_check` (api/routes/health.py) sums SafetyMonitor.get_event_count()
across SafetyMonitor.VALID_EVENT_TYPES via a Redis client built from
`settings.redis_url`, and surfaces the total as `safety_events_last_hour`.
Previously this field was hardcoded to 0 regardless of real Redis activity.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthSafetyEvents:
    """Test suite for the safety_events_last_hour field on /health."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """core.config.settings stand-in with a usable redis_url.

        Also sets redis_host/redis_port so the pre-existing (out-of-scope,
        see PLAN.md) Redis dependency check above the safety-events block
        doesn't itself raise -- these tests are about safety_events_last_hour,
        not that separate bug.
        """
        return MagicMock(
            redis_url="redis://localhost:6379/0",
            redis_host="localhost",
            redis_port=6379,
            vector_db_url="http://localhost:8001",
        )

    def _patch_redis(self, redis_instance: MagicMock) -> MagicMock:
        """Patch redis.Redis so both the dependency check (calls it directly)
        and the safety-events check (calls .from_url) return `redis_instance`.
        """
        mock_redis_class = MagicMock(return_value=redis_instance)
        mock_redis_class.from_url = MagicMock(return_value=redis_instance)
        return mock_redis_class

    @pytest.mark.asyncio
    async def test_no_events_returns_zero(
        self, mock_db: AsyncMock, mock_settings: MagicMock
    ) -> None:
        """No safety events recorded -> count is 0, not an error."""
        redis_instance = MagicMock()
        redis_instance.ping = MagicMock(return_value=True)
        redis_instance.get = MagicMock(return_value=None)

        with (
            patch("redis.Redis", self._patch_redis(redis_instance)),
            patch("core.config.settings", mock_settings),
        ):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 0
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_single_event_type_reflected(
        self, mock_db: AsyncMock, mock_settings: MagicMock
    ) -> None:
        """One recorded pii_detected event shows up in the total."""
        redis_instance = MagicMock()
        redis_instance.ping = MagicMock(return_value=True)
        redis_instance.get = MagicMock(
            side_effect=lambda key: "1" if key == "safety:events:pii_detected" else None
        )

        with (
            patch("redis.Redis", self._patch_redis(redis_instance)),
            patch("core.config.settings", mock_settings),
        ):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 1

    @pytest.mark.asyncio
    async def test_multiple_event_types_summed(
        self, mock_db: AsyncMock, mock_settings: MagicMock
    ) -> None:
        """Counts across different event types are summed, not overwritten."""
        counts = {
            "safety:events:pii_detected": "3",
            "safety:events:injection_attempt": "2",
            "safety:events:bias_detected": "1",
        }
        redis_instance = MagicMock()
        redis_instance.ping = MagicMock(return_value=True)
        redis_instance.get = MagicMock(side_effect=lambda key: counts.get(key))

        with (
            patch("redis.Redis", self._patch_redis(redis_instance)),
            patch("core.config.settings", mock_settings),
        ):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 6

    @pytest.mark.asyncio
    async def test_redis_unavailable_degrades_to_zero_without_failing_health(
        self, mock_db: AsyncMock, mock_settings: MagicMock
    ) -> None:
        """A Redis outage while counting safety events degrades the count to
        0 and does not mark the overall /health response unhealthy -- a
        quiet safety subsystem isn't itself a health-check failure the way a
        down Postgres is.
        """
        redis_instance = MagicMock()
        redis_instance.ping = MagicMock(return_value=True)
        redis_instance.get = MagicMock(side_effect=ConnectionError("redis down"))

        with (
            patch("redis.Redis", self._patch_redis(redis_instance)),
            patch("core.config.settings", mock_settings),
        ):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 0
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_safety_redis_client_construction_failure_does_not_raise(
        self, mock_db: AsyncMock, mock_settings: MagicMock
    ) -> None:
        """If constructing the safety Redis client itself raises, /health
        still responds (count degrades to 0) instead of the request failing.
        """
        redis_instance = MagicMock()
        redis_instance.ping = MagicMock(return_value=True)

        mock_redis_class = MagicMock(return_value=redis_instance)
        mock_redis_class.from_url = MagicMock(side_effect=ConnectionError("cannot connect"))

        with (
            patch("redis.Redis", mock_redis_class),
            patch("core.config.settings", mock_settings),
        ):
            result = await health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 0
        assert result["status"] == "healthy"
