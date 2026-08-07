"""Tests for health.py"""

from unittest.mock import AsyncMock, patch

import pytest

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_postgres_healthy_when_query_succeeds(self) -> None:
        """Test postgres reports healthy when db.execute succeeds."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)

        with patch("core.config.settings") as mock_settings:
            mock_settings.vector_db_url = "http://fake-vector-db"
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379

            result = await health_check(db=mock_db)

        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_check_uses_text_wrapped_query_not_raw_string(self) -> None:
        """Regression test: ensure the postgres probe passes a TextClause,
        not a bare string, to satisfy SQLAlchemy 2.x requirements."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)

        with patch("core.config.settings") as mock_settings:
            mock_settings.vector_db_url = "http://fake-vector-db"
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379

            await health_check(db=mock_db)

        called_arg = mock_db.execute.call_args[0][0]
        # A bare string here would reproduce the original bug (#154)
        assert not isinstance(called_arg, str)
        assert "SELECT 1" in str(called_arg)
