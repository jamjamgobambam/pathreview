"""Tests for the health-check route."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_executes_postgres_probe_as_sqlalchemy_text() -> None:
    """Verify the PostgreSQL probe uses a SQLAlchemy TextClause."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_redis_client = Mock()
    mock_redis_client.ping.return_value = True

    mock_settings = SimpleNamespace(
        redis_host="localhost",
        redis_port=6379,
        vector_db_url="http://vector-db",
    )

    with (
        patch("redis.Redis", return_value=mock_redis_client),
        patch("core.config.settings", mock_settings),
    ):
        result = await health_check(db=mock_db)

    mock_db.execute.assert_awaited_once()

    executed_statement = mock_db.execute.call_args.args[0]

    assert isinstance(executed_statement, TextClause)
    assert str(executed_statement) == "SELECT 1"
    assert result["status"] == "healthy"
    assert result["dependencies"]["postgres"] == "healthy"
