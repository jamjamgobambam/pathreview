"""Tests for the /health endpoint dependency probes."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the health_check route handler."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_settings(self):
        """Create a stand-in for core.config.settings used by the probes.

        ``health_check`` imports ``settings`` inside the request body, so
        patching the module attribute is enough to intercept it.
        """
        settings = Mock()
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        settings.vector_db_url = "http://localhost:8001"
        return settings

    @pytest.fixture
    def healthy_dependencies(self, mock_settings):
        """Patch Redis and settings so Postgres is the only probe under test."""
        with patch("core.config.settings", mock_settings), patch("redis.Redis") as mock_redis_cls:
            mock_redis_cls.return_value.ping = Mock(return_value=True)
            yield mock_redis_cls

    @pytest.mark.asyncio
    async def test_postgres_probe_wraps_sql_in_text_construct(
        self, mock_db_session, healthy_dependencies
    ):
        """Regression test for #154: the probe must pass a text() construct.

        SQLAlchemy 2.x rejects a bare string with ArgumentError, which made the
        endpoint report a reachable database as down.
        """
        await health_check(db=mock_db_session)

        mock_db_session.execute.assert_called_once()
        call_arg = mock_db_session.execute.call_args[0][0]
        assert isinstance(call_arg, TextClause)
        assert not isinstance(call_arg, str)

    @pytest.mark.asyncio
    async def test_postgres_probe_executes_select_1(self, mock_db_session, healthy_dependencies):
        """Test the probe still issues SELECT 1 after being wrapped in text()."""
        await health_check(db=mock_db_session)

        call_arg = mock_db_session.execute.call_args[0][0]
        assert str(call_arg) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_returns_healthy_when_all_probes_succeed(
        self, mock_db_session, healthy_dependencies
    ):
        """Test a reachable database yields an overall healthy response."""
        result = await health_check(db=mock_db_session)

        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_raises_503_when_postgres_probe_fails(
        self, mock_db_session, healthy_dependencies
    ):
        """Test an unreachable database surfaces as HTTP 503."""
        mock_db_session.execute = AsyncMock(side_effect=Exception("connection refused"))

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_503_detail_reports_postgres_unhealthy(
        self, mock_db_session, healthy_dependencies
    ):
        """Test the 503 body identifies Postgres as the failing dependency."""
        mock_db_session.execute = AsyncMock(side_effect=Exception("connection refused"))

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        assert exc_info.value.detail["status"] == "unhealthy"
        assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
