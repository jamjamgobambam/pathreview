"""Tests for the /health route's database probe (issue #154).

The PostgreSQL health probe must execute its liveness query as a SQLAlchemy
textual clause. Under SQLAlchemy 2.x, passing a raw string to
``Session.execute`` raises ``ArgumentError``, which the handler would swallow
and report the database as unhealthy even when it is reachable.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


async def _run_health_check(db):
    """Invoke the handler and return its status dict.

    The handler raises ``HTTPException`` (503) when any dependency is down and
    stashes the status dict in ``detail``; unwrap it so these tests can assert
    on the PostgreSQL result without being coupled to the other dependencies.
    """
    try:
        return await health_check(db=db)
    except HTTPException as exc:
        return exc.detail


@pytest.mark.unit
class TestHealthCheckDatabaseProbe:
    """Test suite for the PostgreSQL probe in the health check route."""

    @pytest.fixture
    def healthy_db(self):
        """A mock async session whose execute() succeeds."""
        session = AsyncMock()
        session.execute = AsyncMock(return_value=Mock())
        return session

    @pytest.mark.asyncio
    async def test_probe_wraps_query_in_text_clause(self, healthy_db):
        """The probe must pass a SQLAlchemy TextClause, not a raw string.

        This is the regression guard for #154: a bare ``"SELECT 1"`` string
        raises ArgumentError under SQLAlchemy 2.x.
        """
        await _run_health_check(healthy_db)

        healthy_db.execute.assert_awaited_once()
        executed = healthy_db.execute.await_args.args[0]
        assert isinstance(executed, TextClause), "health probe must wrap SQL in sqlalchemy.text()"
        assert str(executed) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_postgres_reported_healthy_when_query_succeeds(self, healthy_db):
        """A successful probe reports postgres as healthy."""
        result = await _run_health_check(healthy_db)
        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_reported_unhealthy_when_query_fails(self):
        """A failing probe reports postgres as unhealthy (and does not crash)."""
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("connection refused"))

        result = await _run_health_check(db)
        assert result["dependencies"]["postgres"] == "unhealthy"
