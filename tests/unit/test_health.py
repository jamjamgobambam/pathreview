"""Tests for the health check route (api/routes/health.py)."""

from contextlib import suppress
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheckPostgresProbe:
    """Test suite for the postgres dependency check in health_check().

    Regression coverage for #154: db.execute() was being called with a
    raw Python string ("SELECT 1") instead of a sqlalchemy.text() clause.
    SQLAlchemy 2.x raises ArgumentError for bare strings, which was being
    silently caught by health_check()'s broad except block and reported
    as "unhealthy" even when the database was reachable.

    NOTE: health_check() also checks Redis, which independently raises
    AttributeError today because Settings only defines `redis_url`, not
    `redis_host`/`redis_port` (a separate, pre-existing bug unrelated to
    #154). That means health_check() currently always raises
    HTTPException(503) regardless of the postgres fix. These tests catch
    that HTTPException and inspect its `.detail` payload so the postgres
    assertions aren't coupled to the unrelated redis bug.
    """

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_postgres_probe_uses_text_clause_not_raw_string(self, mock_db_session):
        """db.execute() must be called with sqlalchemy.text(...), not a bare string.

        A raw string would pass silently against an AsyncMock (mocks don't
        enforce SQLAlchemy's argument validation), so this test checks the
        actual type of the argument passed rather than relying on execute()
        to raise.
        """
        with suppress(HTTPException):
            await health_check(db=mock_db_session)
        # (HTTPException expected today, due to the unrelated redis bug — see class docstring)

        mock_db_session.execute.assert_awaited_once()
        executed_statement = mock_db_session.execute.call_args[0][0]

        assert isinstance(executed_statement, TextClause), (
            "db.execute() must be called with sqlalchemy.text('SELECT 1'), "
            f"not a raw string. Got: {type(executed_statement)!r}"
        )
        assert str(executed_statement) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_reports_postgres_healthy_when_probe_succeeds(self, mock_db_session):
        """When the DB probe succeeds, dependencies.postgres should be 'healthy'."""
        try:
            result = await health_check(db=mock_db_session)
        except HTTPException as exc:
            result = exc.detail

        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_reports_postgres_unhealthy_when_probe_raises(self, mock_db_session):
        """When the DB probe genuinely fails, postgres should still be reported unhealthy."""
        mock_db_session.execute.side_effect = ConnectionError("could not connect to server")

        try:
            result = await health_check(db=mock_db_session)
        except HTTPException as exc:
            result = exc.detail

        assert result["dependencies"]["postgres"] == "unhealthy"
        assert result["status"] == "unhealthy"