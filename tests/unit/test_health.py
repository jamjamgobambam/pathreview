"""Tests for the health route."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_postgres_check_uses_text_clause(self) -> None:
        """PostgreSQL check should execute SELECT 1 as a TextClause."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        test_settings = SimpleNamespace(
            redis_host="localhost",
            redis_port=6379,
            vector_db_url="http://vector-db",
        )

        with (
            patch("core.config.settings", test_settings),
            patch("redis.Redis") as mock_redis,
        ):
            mock_redis.return_value.ping.return_value = True
            result = await health_check(db=mock_db)

        mock_db.execute.assert_awaited_once()

        execute_call = mock_db.execute.await_args
        assert execute_call is not None
        statement = execute_call.args[0]

        assert isinstance(statement, TextClause)
        assert str(statement) == "SELECT 1"
        assert result["dependencies"]["postgres"] == "healthy"
