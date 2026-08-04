"""Tests for health endpoint dependency checks."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_returns_healthy_when_dependencies_pass() -> None:
    """Health check should return healthy status when all probes succeed."""
    db = Mock()
    db.execute = AsyncMock()

    redis_client = Mock()
    redis_client.ping.return_value = True

    with (
        patch("redis.Redis.from_url", return_value=redis_client),
        patch("core.config.settings", SimpleNamespace(redis_url="redis://localhost:6379/0", vector_db_url="http://localhost:8001")),
    ):
        result = await health_check(db=db)

    db.execute.assert_awaited_once()
    first_arg = db.execute.await_args.args[0]
    assert first_arg.text == "SELECT 1"
    redis_client.ping.assert_called_once()
    assert result["status"] == "healthy"
    assert result["dependencies"]["postgres"] == "healthy"
    assert result["dependencies"]["redis"] == "healthy"
    assert result["dependencies"]["vector_db"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_raises_503_when_redis_fails() -> None:
    """Health check should surface unhealthy dependencies as HTTP 503."""
    db = Mock()
    db.execute = AsyncMock()

    redis_client = Mock()
    redis_client.ping.side_effect = RuntimeError("redis unavailable")

    with (
        patch("redis.Redis.from_url", return_value=redis_client),
        patch("core.config.settings", SimpleNamespace(redis_url="redis://localhost:6379/0", vector_db_url="http://localhost:8001")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=db)

    assert exc_info.value.status_code == 503
    detail = exc_info.value.detail
    assert detail["status"] == "unhealthy"
    assert detail["dependencies"]["postgres"] == "healthy"
    assert detail["dependencies"]["redis"] == "unhealthy"
