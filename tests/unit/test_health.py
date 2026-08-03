"""Unit tests for the health check endpoint."""
import pytest
from unittest.mock import AsyncMock
from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for health check PostgreSQL database probe."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    async def test_postgres_health_check_uses_text_wrapped_sql(self, mock_db):
        """
        Verify that the health check wraps raw SQL in text() for SQLAlchemy 2.x.
        Before fix: await db.execute("SELECT 1") — fails in SQLAlchemy 2.x
        After fix: await db.execute(text("SELECT 1")) — works correctly
        """
        result = await health_check(db=mock_db)

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0][0]

        assert str(type(call_args)) == "<class 'sqlalchemy.sql.expression.TextClause'>"
        assert "SELECT 1" in str(call_args)
        assert result["dependencies"]["postgres"] == "healthy"

    async def test_postgres_health_check_catches_exceptions(self, mock_db):
        """Verify that database exceptions are caught and reported as unhealthy."""
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))

        result = await health_check(db=mock_db)

        assert result["dependencies"]["postgres"] == "unhealthy"
        assert result["status"] == "unhealthy"