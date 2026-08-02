"""Tests for the health check endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the health endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_postgres_health_check_uses_text_clause(self, mock_db):
        """Verify the PostgreSQL probe executes a SQLAlchemy TextClause."""
        with patch("redis.Redis") as mock_redis, patch("core.config.settings") as mock_settings:

            # Mock Redis
            mock_redis.return_value.ping.return_value = True
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://localhost"

            await health_check(db=mock_db)

        # Database execute should have been called exactly once
        mock_db.execute.assert_awaited_once()

        # Grab the SQL statement passed to execute()
        statement = mock_db.execute.await_args.args[0]

        # Verify it is SQLAlchemy's text() object
        assert isinstance(statement, TextClause)

        # Verify it contains the expected SQL
        assert str(statement) == "SELECT 1"
