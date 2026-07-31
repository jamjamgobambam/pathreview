"""Tests for api/routes/health.py"""
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the health_check route's Postgres probe."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock(return_value=None)
        return session

    @pytest.mark.asyncio
    async def test_postgres_check_healthy_when_query_succeeds(self, mock_db_session):
        """Postgres check should report healthy when execute() succeeds.

        Note: overall status will still be "unhealthy" and health_check()
        will raise HTTPException, because the Redis check has a separate,
        pre-existing bug (issue #155: settings.redis_host does not exist).
        That's expected and out of scope here — we inspect the raised
        exception's detail payload to confirm the Postgres check itself
        is isolated from that failure.
        """
        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        detail = exc_info.value.detail
        assert detail["dependencies"]["postgres"] == "healthy"
        mock_db_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_postgres_check_unhealthy_when_query_raises(self, mock_db_session):
        """Postgres check should report unhealthy if execute() raises."""
        mock_db_session.execute.side_effect = Exception("connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        detail = exc_info.value.detail
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"