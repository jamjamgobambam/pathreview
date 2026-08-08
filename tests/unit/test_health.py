"""Unit tests for api/routes/health.py.

Covers issue #154: the ``GET /health`` PostgreSQL probe must wrap its SQL in
``sqlalchemy.text()`` so it runs under SQLAlchemy 2.x instead of raising
``ArgumentError`` and falsely reporting a reachable database as unhealthy.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import ArgumentError
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


def _status_dict(returned=None, exc=None):
    """Return the health-status payload whether health_check returned or raised.

    The endpoint returns the dict on success and raises HTTPException(detail=dict)
    when any dependency is down. Both carry the same structure, so tests can
    assert on the Postgres key regardless of the aggregate status.
    """
    if exc is not None:
        return exc.detail
    return returned


class _RejectRawStringSession:
    """Async session mimicking SQLAlchemy 2.x execute() semantics.

    Accepts a ``TextClause`` (from ``text()``); rejects a bare ``str`` with
    ``ArgumentError``, exactly as a real 2.x ``AsyncSession`` does. This lets the
    happy-path test double as a regression guard against re-introducing a raw
    string.
    """

    def __init__(self) -> None:
        self.received = None

    async def execute(self, statement):
        self.received = statement
        if isinstance(statement, TextClause):
            return MagicMock()
        raise ArgumentError(
            "Textual SQL expression 'SELECT 1' should be explicitly declared " "as text('SELECT 1')"
        )


@pytest.mark.unit
class TestHealthCheckPostgresProbe:
    """Test suite for the PostgreSQL probe in health_check() (issue #154)."""

    @pytest.mark.asyncio
    async def test_postgres_probe_uses_text_clause_and_reports_healthy(self):
        """A reachable DB is reported healthy and probed with a TextClause.

        Regression guard for #154: if the probe reverts to a raw string, the
        SQLAlchemy-2.x-style session raises ArgumentError and this assertion
        fails.
        """
        db = _RejectRawStringSession()

        # Redis has no server in unit tests; stub it so it doesn't dominate the
        # aggregate status. We only assert on the Postgres dependency here.
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            try:
                returned = await health_check(db=db)
                status = _status_dict(returned=returned)
            except HTTPException as exc:
                status = _status_dict(exc=exc)

        assert isinstance(db.received, TextClause)
        assert status["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_probe_reports_unhealthy_on_db_error(self):
        """A genuine DB failure is still caught and surfaced as 503.

        The fix must not swallow real outages: when execute() raises, Postgres
        is reported unhealthy and the endpoint returns HTTP 503.
        """
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("connection refused"))

        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            with pytest.raises(HTTPException) as excinfo:
                await health_check(db=db)

        assert excinfo.value.status_code == 503
        assert excinfo.value.detail["dependencies"]["postgres"] == "unhealthy"
        assert excinfo.value.detail["status"] == "unhealthy"
