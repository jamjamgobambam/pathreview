"""Tests for the /health route DB probe (api/routes/health.py).

Reproduction test for issue #154:
https://github.com/ascherj/pathreview/issues/154

The health check probes Postgres with ``await db.execute("SELECT 1")`` — a bare
Python string. Under SQLAlchemy 2.x a raw string is no longer an executable
object; it must be wrapped in ``sqlalchemy.text()``. Passing the raw string
raises ``sqlalchemy.exc.ArgumentError`` during statement coercion (before any DB
round-trip), and the route's ``try/except`` swallows it and misreports Postgres
as "unhealthy" even when the database is up.

These tests document today's *broken* behavior. They pass on the current code and
will need their assertions flipped (expecting "healthy") once the fix wraps the
query in ``text("SELECT 1")`` — see PLAN.md.
"""

import pytest
from sqlalchemy import exc as sa_exc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheckRawSQLBug:
    """Reproduce the SQLAlchemy 2.x raw-SQL failure in the health check (#154)."""

    @pytest.fixture
    def async_session_factory(self):
        """A real async session factory built like core.database's.

        The engine points at an unreachable host on purpose. The bug we are
        reproducing surfaces during SQLAlchemy's statement coercion, which
        happens *before* any connection is attempted, so no live database is
        required and the test stays a fast, dependency-free unit test.
        """
        engine = create_async_engine(
            "postgresql+asyncpg://healthcheck:healthcheck@127.0.0.1:1/pathreview_repro",
        )
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @pytest.mark.asyncio
    async def test_raw_string_execute_raises_argument_error(self, async_session_factory):
        """`db.execute("SELECT 1")` raises ArgumentError under SQLAlchemy 2.x (#154).

        Proves the failure comes purely from passing a raw string to execute(),
        not from database connectivity — the error is raised before we connect.
        """
        async with async_session_factory() as session:
            with pytest.raises(sa_exc.ArgumentError) as exc_info:
                await session.execute("SELECT 1")

        # SQLAlchemy 2.x tells us exactly how to fix it: wrap in text().
        assert "text(" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check_reports_db_unhealthy_due_to_raw_sql_string(
        self, async_session_factory
    ):
        """The route swallows the ArgumentError and misreports Postgres (#154).

        Confirms the bug's user-visible impact: even though the ArgumentError is
        an API misuse (not a real connectivity problem), the surrounding
        try/except catches it and marks Postgres — and the overall service — as
        "unhealthy", returning HTTP 503.
        """
        async with async_session_factory() as session:
            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=session)

        detail = exc_info.value.detail
        assert exc_info.value.status_code == 503
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"
