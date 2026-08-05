"""Unit tests for the health check route."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Tests for the health check endpoint."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock asynchronous database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_settings(self) -> SimpleNamespace:
        """Provide the settings used by the other dependency checks."""
        return SimpleNamespace(
            redis_host="localhost",
            redis_port=6379,
            vector_db_url="http://localhost:8001",
        )

    @pytest.mark.asyncio
    async def test_postgres_probe_uses_text_clause(
        self,
        mock_db_session: AsyncMock,
        mock_settings: SimpleNamespace,
    ) -> None:
        """The PostgreSQL probe should execute SELECT 1 as a TextClause."""
        with (
            patch("core.config.settings", mock_settings),
            patch("redis.Redis") as mock_redis,
        ):
            mock_redis.return_value.ping.return_value = True
            result = await health_check(mock_db_session)

        mock_db_session.execute.assert_awaited_once()
        statement = mock_db_session.execute.await_args.args[0]

        assert isinstance(statement, TextClause)
        assert str(statement) == "SELECT 1"
        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_failure_returns_503(
        self,
        mock_db_session: AsyncMock,
        mock_settings: SimpleNamespace,
    ) -> None:
        """A genuine PostgreSQL failure should still return a 503 response."""
        mock_db_session.execute.side_effect = RuntimeError("database unavailable")

        with (
            patch("core.config.settings", mock_settings),
            patch("redis.Redis") as mock_redis,
        ):
            mock_redis.return_value.ping.return_value = True

            with pytest.raises(HTTPException) as exc_info:
                await health_check(mock_db_session)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["status"] == "unhealthy"
        assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
