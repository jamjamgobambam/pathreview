"""Tests for the health check endpoint."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check
from core.config import settings


@pytest.mark.unit
class TestHealthCheck:
    """Verify the health route uses the current dependency configuration."""

    @pytest.mark.asyncio
    async def test_health_check_uses_redis_url_and_text_query_for_healthy_status(self) -> None:
        """Build the Redis client from settings.redis_url and use a SQLAlchemy text query."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        redis_client = Mock()
        redis_client.ping = Mock(return_value=True)

        with patch("redis.Redis.from_url", return_value=redis_client) as from_url:
            result = await health_check(db)

        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"
        assert result["dependencies"]["redis"] == "healthy"
        assert result["dependencies"]["vector_db"] == "healthy"

        stmt = db.execute.call_args.args[0]
        assert isinstance(stmt, TextClause)
        assert str(stmt) == "SELECT 1"

        from_url.assert_called_once_with(settings.redis_url)
        redis_client.ping.assert_called_once_with()
