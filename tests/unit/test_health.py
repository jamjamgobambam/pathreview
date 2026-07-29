"""Reproduction tests for the health check endpoint."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheckReproduction:
    """Capture the current Redis settings mismatch in the health route."""

    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_redis_host_setting_is_missing(self) -> None:
        """Reproduce the current failure mode for the Redis dependency probe."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)

        assert not hasattr(settings, "redis_host")

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["status"] == "unhealthy"
        assert exc_info.value.detail["dependencies"]["postgres"] == "healthy"
        assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
        assert exc_info.value.detail["dependencies"]["vector_db"] == "healthy"
