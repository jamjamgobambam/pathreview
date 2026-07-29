"""Reproduction test for issue #155.

api/routes/health.py's Redis probe references settings.redis_host and
settings.redis_port, but core/config.py's Settings model only defines
redis_url — the host/port fields don't exist. The AttributeError this
causes is swallowed by the route's broad `except Exception` block, so
instead of a clean crash, the endpoint silently marks Redis (and therefore
the whole health check) "unhealthy" and returns a 503 — even when Redis
is actually running fine.

These tests document that CURRENT (broken) behavior ahead of the Week 9
fix. See: https://github.com/ascherj/pathreview/issues/155
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheckRedisBug:
    """Reproduces issue #155: health check crashes on nonexistent settings fields."""

    def test_settings_has_no_redis_host_or_port_field(self) -> None:
        """Confirms the root cause: Settings only defines redis_url, not redis_host/redis_port."""
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")
        assert hasattr(settings, "redis_url")

    @pytest.mark.asyncio
    async def test_health_check_reports_unhealthy_due_to_swallowed_attribute_error(self) -> None:
        """Reproduces the bug end-to-end.

        Even with Postgres reachable, the health check raises a 503 because the
        Redis probe's AttributeError (settings.redis_host doesn't exist) gets
        caught by the route's broad except block and marks "redis" (and
        therefore the overall status) unhealthy.
        """
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        detail = exc_info.value.detail
        assert exc_info.value.status_code == 503
        assert detail["dependencies"]["postgres"] == "healthy"
        # This should be "healthy" once the fix lands; today it's always "unhealthy".
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["status"] == "unhealthy"
