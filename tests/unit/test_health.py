"""Unit tests for the health check endpoint."""
import pytest
from unittest.mock import AsyncMock
from sqlalchemy import text
from api.routes.health import health_check


@pytest.mark.asyncio
async def test_postgres_health_check_uses_text_wrapped_sql():
    """
    Verify that the health check wraps raw SQL in text() for SQLAlchemy 2.x.
    """
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)
    
    result = await health_check(db=mock_db)
    
    mock_db.execute.assert_called_once()
    call_args = mock_db.execute.call_args[0][0]
    
    assert str(type(call_args)) == "<class 'sqlalchemy.sql.expression.TextClause'>"
    assert "SELECT 1" in str(call_args)
    assert result["dependencies"]["postgres"] == "healthy"


@pytest.mark.asyncio
async def test_postgres_health_check_catches_exceptions():
    """Verify that database exceptions are caught and logged."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))
    
    result = await health_check(db=mock_db)
    
    assert result["dependencies"]["postgres"] == "unhealthy"
    assert result["status"] == "unhealthy"