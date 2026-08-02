"""Tests for the /health endpoint (api/routes/health.py)."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from api.routes.health import health_check


class FakeAsyncSession:
    """Minimal stand-in for an AsyncSession, so we don't need a live DB for unit tests."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.executed_with: list[Any] = []

    async def execute(self, *args: Any, **kwargs: Any) -> MagicMock:
        self.executed_with.append(args[0] if args else None)
        if self.should_fail:
            raise OperationalError("connection refused", None, None)
        return MagicMock()


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the GET /health endpoint."""

    @pytest.fixture
    def healthy_session(self) -> FakeAsyncSession:
        return FakeAsyncSession(should_fail=False)

    @pytest.fixture
    def broken_session(self) -> FakeAsyncSession:
        return FakeAsyncSession(should_fail=True)

    @pytest.mark.asyncio
    async def test_all_dependencies_healthy_returns_200(
        self, healthy_session: FakeAsyncSession
    ) -> None:
        """Test all dependencies reachable returns healthy status."""
        with (
            patch("redis.Redis.from_url") as mock_from_url,
            patch("core.config.settings") as mock_settings,
        ):
            mock_settings.redis_url = "redis://localhost:6379/0"
            mock_settings.vector_db_url = "http://localhost:8001"

            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_from_url.return_value = mock_redis_client

            result = await health_check(db=healthy_session)

        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"
        assert result["dependencies"]["redis"] == "healthy"
        assert result["dependencies"]["vector_db"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_down_returns_503(self, broken_session: FakeAsyncSession) -> None:
        """Test Postgres query failure returns 503 with postgres marked unhealthy."""
        with (
            patch("redis.Redis.from_url") as mock_from_url,
            patch("core.config.settings") as mock_settings,
        ):
            mock_settings.redis_url = "redis://localhost:6379/0"
            mock_settings.vector_db_url = "http://localhost:8001"

            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_from_url.return_value = mock_redis_client

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=broken_session)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["postgres"] == "unhealthy"
        # Redis should still be correctly reported, independent of postgres failing
        assert detail["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_down_returns_503(self, healthy_session: FakeAsyncSession) -> None:
        """Test Redis ping failure returns 503 with redis marked unhealthy."""
        with (
            patch("redis.Redis.from_url") as mock_from_url,
            patch("core.config.settings") as mock_settings,
        ):
            mock_settings.redis_url = "redis://localhost:6379/0"
            mock_settings.vector_db_url = "http://localhost:8001"

            mock_redis_client = MagicMock()
            mock_redis_client.ping.side_effect = ConnectionError("connection refused")
            mock_from_url.return_value = mock_redis_client

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=healthy_session)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["status"] == "unhealthy"
        assert detail["dependencies"]["redis"] == "unhealthy"
        # Postgres should still be correctly reported, independent of redis failing
        assert detail["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_vector_db_unavailable_when_url_missing(
        self, healthy_session: FakeAsyncSession
    ) -> None:
        """Test missing vector_db_url reports vector_db as unavailable, not a hard failure."""
        with (
            patch("redis.Redis.from_url") as mock_from_url,
            patch("core.config.settings") as mock_settings,
        ):
            mock_settings.redis_url = "redis://localhost:6379/0"
            mock_settings.vector_db_url = None

            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_from_url.return_value = mock_redis_client

            result = await health_check(db=healthy_session)

        assert result["dependencies"]["vector_db"] == "unavailable"
        # Current implementation treats "unavailable" as non-fatal; overall status stays healthy
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_check_uses_text_wrapped_sql(
        self, healthy_session: FakeAsyncSession
    ) -> None:
        """Test Postgres check passes a sqlalchemy.text() construct, not a raw string.

        Regression test: SQLAlchemy 2.x raises ArgumentError if textual SQL isn't
        explicitly wrapped in text().
        """
        with (
            patch("redis.Redis.from_url") as mock_from_url,
            patch("core.config.settings") as mock_settings,
        ):
            mock_settings.redis_url = "redis://localhost:6379/0"
            mock_settings.vector_db_url = "http://localhost:8001"

            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_from_url.return_value = mock_redis_client

            await health_check(db=healthy_session)

            called_arg = healthy_session.executed_with[0]
            # A raw string would fail this check; SQLAlchemy's TextClause has a `.text` attribute
            assert hasattr(
                called_arg, "text"
            ), "Postgres check must pass a sqlalchemy.text() construct, not a raw string"
