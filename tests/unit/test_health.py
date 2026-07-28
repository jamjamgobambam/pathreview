"""Tests for api/routes/health.py"""

from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the postgres branch of health_check()."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_postgres_query_is_wrapped_in_text(self, mock_db_session: AsyncMock) -> None:
        """db.execute() must receive a TextClause, not a bare string.

        SQLAlchemy 2.x raises ObjectNotExecutableError for raw strings, so a
        regression here would silently flip postgres back to "unhealthy".
        """
        with pytest.raises(HTTPException):
            await health_check(db=mock_db_session)

        call_args = mock_db_session.execute.call_args[0]
        query = call_args[0]
        assert isinstance(query, TextClause)
        assert str(query) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_postgres_marked_healthy_when_query_succeeds(
        self, mock_db_session: AsyncMock
    ) -> None:
        """A successful query should mark postgres healthy, independent of
        the unrelated redis config bug that also fails this endpoint."""
        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        detail = cast("dict", exc_info.value.detail)
        assert detail["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_marked_unhealthy_when_query_raises(
        self, mock_db_session: AsyncMock
    ) -> None:
        """A real connectivity failure must still surface as unhealthy."""
        mock_db_session.execute.side_effect = ConnectionError("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db_session)

        detail = cast("dict", exc_info.value.detail)
        assert exc_info.value.status_code == 503
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"
