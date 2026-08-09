"""Tests for the PostgreSQL probe in ``api/routes/health.py`` (issue #154).

https://github.com/ascherj/pathreview/issues/154

The health check verified PostgreSQL by running ``await db.execute("SELECT 1")``
-- passing the query as a plain Python string. SQLAlchemy 2.x refuses to execute
a bare string; textual SQL must be wrapped in ``sqlalchemy.text()``. Because of
this the Postgres probe always raised, the health check reported the database as
"unhealthy", and ``GET /health`` returned HTTP 503 even when the database was up.

These tests drive ``health_check()`` with a stub async session that enforces the
same rule SQLAlchemy 2.x does, so no live PostgreSQL is required. They assert
specifically on the ``postgres`` dependency value rather than the overall status
code, because the Redis probe in the same endpoint has a separate, unrelated bug
(issue #155) that independently forces the endpoint to 503.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ObjectNotExecutableError, OperationalError
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


class StubResult:
    """Minimal stand-in for a SQLAlchemy ``Result``."""

    def scalar(self) -> int:
        """Return the single value a ``SELECT 1`` probe would produce."""
        return 1


class StubAsyncSession:
    """Async session stub that mimics SQLAlchemy 2.x ``execute()`` strictness.

    Records every statement it is handed and rejects bare strings the same way
    SQLAlchemy 2.x does, so a regression back to ``execute("SELECT 1")`` fails
    these tests instead of silently passing.

    Args:
        raise_on_execute: Optional exception raised by ``execute()``, used to
            simulate a database that is genuinely unreachable.
    """

    def __init__(self, raise_on_execute: Exception | None = None) -> None:
        self.executed: list[object] = []
        self._raise_on_execute = raise_on_execute

    async def execute(self, statement: object) -> StubResult:
        """Record and "run" a statement, rejecting non-executable objects."""
        if self._raise_on_execute is not None:
            raise self._raise_on_execute
        if isinstance(statement, str):
            raise ObjectNotExecutableError(statement)
        self.executed.append(statement)
        return StubResult()


async def _run_health_check(db: StubAsyncSession) -> dict:
    """Call the endpoint and return its payload whether it returns 200 or 503.

    The endpoint raises ``HTTPException`` when any dependency is unhealthy, and
    the Redis probe is independently broken by issue #155. Unwrapping the detail
    lets these tests assert on the Postgres probe alone.

    Args:
        db: The stub session to inject as the ``db`` dependency.

    Returns:
        The health status payload produced by ``health_check()``.
    """
    try:
        return await health_check(db=db)
    except HTTPException as exc:
        assert isinstance(exc.detail, dict)
        return exc.detail


@pytest.mark.unit
class TestPostgresHealthProbe:
    """Test suite for the PostgreSQL dependency probe."""

    @pytest.mark.asyncio
    async def test_postgres_reported_healthy_when_database_reachable(self) -> None:
        """Issue #154: a reachable database must be reported as healthy."""
        db = StubAsyncSession()

        health_status = await _run_health_check(db)

        assert health_status["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_probe_wraps_query_in_text_clause(self) -> None:
        """The probe must pass a ``TextClause``, not a raw string."""
        db = StubAsyncSession()

        await _run_health_check(db)

        assert len(db.executed) == 1
        statement = db.executed[0]
        assert isinstance(statement, TextClause)
        assert str(statement) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_postgres_reported_unhealthy_when_database_down(self) -> None:
        """A genuine outage must still be reported: the fix must not mask it."""
        outage = OperationalError("SELECT 1", None, Exception("connection refused"))
        db = StubAsyncSession(raise_on_execute=outage)

        health_status = await _run_health_check(db)

        assert health_status["dependencies"]["postgres"] == "unhealthy"
        assert health_status["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_endpoint_returns_503_when_database_down(self) -> None:
        """A database outage must still surface as HTTP 503."""
        outage = OperationalError("SELECT 1", None, Exception("connection refused"))
        db = StubAsyncSession(raise_on_execute=outage)

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=db)

        assert exc_info.value.status_code == 503


@pytest.mark.unit
class TestSqlAlchemyTextRequirement:
    """Root-cause tests documenting the SQLAlchemy 2.x rule behind issue #154."""

    def test_raw_string_select_is_rejected(self) -> None:
        """A bare string is not executable, which is what broke the probe."""
        engine = create_engine("sqlite://")
        with engine.connect() as conn, pytest.raises(ObjectNotExecutableError):
            conn.execute("SELECT 1")

    def test_text_wrapped_select_executes(self) -> None:
        """Wrapping the query in ``text()`` executes correctly -- the fix."""
        engine = create_engine("sqlite://")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
