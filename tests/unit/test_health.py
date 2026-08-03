"""Unit tests for the health check endpoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
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
        """Verify db.execute is called with a SQLAlchemy text() object."""
        from api.routes.health import health_check
        
        with patch("core.config.settings") as mock_settings:
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://localhost:8000"
            
            with patch("redis.Redis") as mock_redis:
                mock_redis.return_value.ping = MagicMock()
                
                try:
                    await health_check(db=mock_db)
                except HTTPException:
                    pass
        
        # Verify text() was used
        mock_db.execute.assert_called_once()
        call_arg = mock_db.execute.call_args[0][0]
        assert isinstance(call_arg, TextClause)

    async def test_postgres_probe_catches_db_exception(self, mock_db):
        """Verify postgres is marked unhealthy when db.execute raises."""
        from api.routes.health import health_check
        
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))
        
        with patch("core.config.settings") as mock_settings:
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://localhost:8000"
            
            with patch("redis.Redis") as mock_redis:
                mock_redis.return_value.ping = MagicMock()
                
                with pytest.raises(HTTPException) as exc_info:
                    await health_check(db=mock_db)
                
                assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"