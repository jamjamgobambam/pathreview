"""Unit tests for the health check endpoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.sql.expression import TextClause
from fastapi import HTTPException


@pytest.mark.unit
class TestHealthCheck:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    async def test_postgres_probe_uses_text_object(self, mock_db):
        """Verify db.execute is called with text() for SQLAlchemy 2.x compatibility."""
        from api.routes.health import health_check
        
        with patch("api.routes.health.redis.Redis") as mock_redis_class:
            mock_redis_class.return_value.ping = MagicMock()
            
            try:
                await health_check(db=mock_db)
            except HTTPException as exc:
                # Postgres check should pass even if redis fails
                assert exc.detail["dependencies"]["postgres"] == "healthy"
        
        # Verify text() wrapper was used
        mock_db.execute.assert_called_once()
        call_arg = mock_db.execute.call_args[0][0]
        assert isinstance(call_arg, TextClause), (
            f"Expected TextClause but got {type(call_arg).__name__}. "
            "SQLAlchemy 2.x requires text('SELECT 1') not raw strings."
        )

    async def test_postgres_probe_catches_db_exception(self, mock_db):
        """Verify postgres marked unhealthy when db.execute fails."""
        from api.routes.health import health_check
        
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))
        
        with patch("api.routes.health.redis.Redis") as mock_redis_class:
            mock_redis_class.return_value.ping = MagicMock()
            
            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=mock_db)
            
            # When postgres fails, it should be marked unhealthy
            assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
            assert exc_info.value.detail["status"] == "unhealthy"