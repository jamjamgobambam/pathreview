"""Tests for health.py endpoint."""

from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for health check endpoint."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_settings_config(self) -> Mock:
        """Create mock settings configuration."""
        settings = Mock()
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        settings.vector_db_url = "http://localhost:6333"
        return settings

    @pytest.mark.asyncio
    async def test_health_check_all_services_healthy_returns_200(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test health check returns 200 when all services are healthy."""
        mock_db.execute = AsyncMock()

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
        ):

            mock_redis.return_value.ping = Mock()

            result = await health_check(db=mock_db)

            assert result["status"] == "healthy"
            assert result["dependencies"]["postgres"] == "healthy"
            assert result["dependencies"]["redis"] == "healthy"
            assert result["dependencies"]["vector_db"] == "healthy"
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_postgres_down_returns_503(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test health check returns 503 when PostgreSQL is down."""
        mock_db.execute = AsyncMock(side_effect=Exception("Connection refused"))

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
        ):

            mock_redis.return_value.ping = Mock()

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=mock_db)

            assert exc_info.value.status_code == 503
            detail = cast("dict", exc_info.value.detail)
            assert detail["status"] == "unhealthy"
            assert detail["dependencies"]["postgres"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_redis_down_returns_503(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test health check returns 503 when Redis is down."""
        mock_db.execute = AsyncMock()

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
        ):

            mock_redis.side_effect = Exception("Redis connection failed")

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=mock_db)

            assert exc_info.value.status_code == 503
            detail = cast("dict", exc_info.value.detail)
            assert detail["status"] == "unhealthy"
            assert detail["dependencies"]["redis"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_vector_db_unavailable_still_healthy(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test health check returns 200 when vector_db URL is not set."""
        mock_db.execute = AsyncMock()
        mock_settings_config.vector_db_url = None

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
        ):

            mock_redis.return_value.ping = Mock()

            result = await health_check(db=mock_db)

            assert result["status"] == "healthy"
            assert result["dependencies"]["vector_db"] == "unavailable"

    @pytest.mark.asyncio
    async def test_health_check_response_includes_timestamp(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test health check response includes ISO format timestamp."""
        mock_db.execute = AsyncMock()

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
        ):

            mock_redis.return_value.ping = Mock()

            result = await health_check(db=mock_db)

            assert "timestamp" in result
            assert "T" in result["timestamp"]  # ISO format check

    @pytest.mark.asyncio
    async def test_health_check_response_includes_safety_events(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test health check response includes safety events count."""
        mock_db.execute = AsyncMock()

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
        ):

            mock_redis.return_value.ping = Mock()

            result = await health_check(db=mock_db)

            assert "safety_events_last_hour" in result
            assert isinstance(result["safety_events_last_hour"], int)

    @pytest.mark.asyncio
    async def test_health_check_postgres_uses_text_wrapper(
        self, mock_db: AsyncMock, mock_settings_config: Mock
    ) -> None:
        """Test that PostgreSQL check uses sqlalchemy.text() wrapper."""
        mock_db.execute = AsyncMock()

        with (
            patch("redis.Redis") as mock_redis,
            patch("core.config.settings", mock_settings_config),
            patch("api.routes.health.text") as mock_text,
        ):

            mock_redis.return_value.ping = Mock()

            await health_check(db=mock_db)

            mock_text.assert_called_once_with("SELECT 1")
            mock_db.execute.assert_called_once()
