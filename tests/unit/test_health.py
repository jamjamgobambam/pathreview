"""Unit tests for the health endpoint."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_executes_textual_sql() -> None:
    """The PostgreSQL probe should execute an SQLAlchemy text statement."""
    db = AsyncMock()
    fake_settings = SimpleNamespace(
        redis_host="localhost",
        redis_port=6379,
        vector_db_url="http://localhost:8001",
    )
    redis_client = Mock()

    with (
        patch("api.routes.health.settings", fake_settings),
        patch("api.routes.health.redis.Redis", return_value=redis_client),
    ):
        result = await health_check(db)

    db.execute.assert_awaited_once()
    statement = db.execute.await_args.args[0]

    assert not isinstance(statement, str)
    assert str(statement) == "SELECT 1"
    assert result["dependencies"]["postgres"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_marks_postgres_unhealthy_on_database_error() -> None:
    """A genuine database failure should still produce an unhealthy response."""
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("database unavailable")

    fake_settings = SimpleNamespace(
        redis_host="localhost",
        redis_port=6379,
        vector_db_url="http://localhost:8001",
    )
    redis_client = Mock()

    with (
        patch("api.routes.health.settings", fake_settings),
        patch("api.routes.health.redis.Redis", return_value=redis_client),
        pytest.raises(HTTPException) as exc_info,
    ):
        await health_check(db)

    assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
