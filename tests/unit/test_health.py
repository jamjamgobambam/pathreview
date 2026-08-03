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
        """Verify db.execute is called with a SQLAlchemy text() object.
        
        Fix for issue #154: SQLAlchemy 2.x requires text() wrapper.
        """
        from api.routes.health import health_check
        
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping = MagicMock()
            try:
                await health_check(db=mock_db)
            except HTTPException:
                pass  # Expected — redis will fail, but postgres should pass
        
        # Verify postgres check used text() object
        mock_db.execute.assert_called_once()
        call_arg = mock_db.execute.call_args[0][0]
        assert isinstance(call_arg, TextClause), (
            f"Expected text() wrapper but got {type(call_arg).__name__}"
        )

    async def test_postgres_probe_catches_db_exception(self, mock_db):
        """Verify postgres is marked unhealthy when db.execute raises."""
        from api.routes.health import health_check
        
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))
        
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping = MagicMock()
            try:
                await health_check(db=mock_db)
            except HTTPException as exc:
                # Inspect the error response
                assert exc.detail["dependencies"]["postgres"] == "unhealthy"
                assert exc.detail["status"] == "unhealthy"
                return
        
        pytest.fail("Expected HTTPException to be raised")