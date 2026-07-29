"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_redis_check_fails_due_to_missing_settings_field(self) -> None:
        """Reproduces issue #155.

        health.py reads settings.redis_host, but Settings only defines
        redis_url. This means the redis health check always fails with
        an AttributeError, even when Redis itself is running fine, and
        the overall /health response is always reported as unhealthy.
        """
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        detail = exc_info.value.detail
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["status"] == "unhealthy"
