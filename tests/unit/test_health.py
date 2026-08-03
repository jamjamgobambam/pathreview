"""Unit tests for the health check endpoint."""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.sql.expression import TextClause


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for health check PostgreSQL database probe."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    async def test_postgres_probe_uses_text_object(self, mock_db):
        """
        Verify db.execute is called with a SQLAlchemy text() object, not a raw string.
        Fix for issue #154: SQLAlchemy 2.x requires text() wrapper.
        """
        from api.routes.health import health_check
        await health_check(db=mock_db)

        mock_db.execute.assert_called_once()
        call_arg = mock_db.execute.call_args[0][0]

        assert isinstance(call_arg, TextClause), (
            f"Expected TextClause but got {type(call_arg)}. "
            "Raw SQL strings fail in SQLAlchemy 2.x — use text('SELECT 1')."
        )

    async def test_postgres_probe_catches_db_exception(self, mock_db):
        """Verify database exceptions are caught and postgres marked unhealthy."""
        from api.routes.health import health_check
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))

        result = await health_check(db=mock_db)

        assert result["dependencies"]["postgres"] == "unhealthy"
        assert result["status"] == "unhealthy"