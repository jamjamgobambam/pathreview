"""Unit tests for the health check endpoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import text
from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for health check PostgreSQL database probe."""

    @pytest.mark.asyncio
    async def test_postgres_health_check_uses_text_wrapped_sql(self):
        """
        Verify that the health check wraps raw SQL in text() for SQLAlchemy 2.x.
        
        This test ensures the fix for issue #154 is working:
        - Before: await db.execute("SELECT 1") — fails in SQLAlchemy 2.x
        - After: await db.execute(text("SELECT 1")) — works correctly
        """
        # Mock the database session
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=None)
        
        # Call health check with mocked db
        result = await health_check(db=mock_db)
        
        # Verify text() was called with "SELECT 1"
        mock_db.execute.assert_called_once()
        
        # Get the actual argument passed to execute
        call_args = mock_db.execute.call_args[0][0]
        
        # Verify it's a text() object, not a raw string
        assert str(type(call_args)) == "<class 'sqlalchemy.sql.expression.TextClause'>"
        assert "SELECT 1" in str(call_args)
        
        # Verify postgres was marked healthy
        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_health_check_catches_exceptions(self):
        """Verify that database exceptions are caught and logged."""
        # Mock the database session to raise an exception
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))
        
        # Call health check
        result = await health_check(db=mock_db)
        
        # Verify postgres marked as unhealthy
        assert result["dependencies"]["postgres"] == "unhealthy"
        assert result["status"] == "unhealthy"