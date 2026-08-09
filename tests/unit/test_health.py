"""Tests for api/routes/health.py"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint's Postgres probe."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_postgres_reports_healthy_when_query_succeeds(
        self, mock_db_session: AsyncMock
    ) -> None:
        """When db.execute succeeds, postgres should be reported as healthy."""
        try:
            result = await health_check(db=mock_db_session)  # type: ignore[arg-type]
        except HTTPException as exc:
            result = exc.detail

        mock_db_session.execute.assert_awaited_once()
        stmt = mock_db_session.execute.call_args.args[0]
        assert getattr(stmt, "text", None) == "SELECT 1"

        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_reports_unhealthy_when_query_raises(
        self, mock_db_session: AsyncMock
    ) -> None:
        """When db.execute raises, postgres should be reported as unhealthy
        and the endpoint should raise HTTPException with a 503 status."""
        mock_db_session.execute.side_effect = Exception("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
