"""Reproduction test for issue #154.

api/routes/health.py:31 calls `await db.execute("SELECT 1")` with a raw
Python string. SQLAlchemy 2.x no longer accepts raw strings as SQL — the
string must be wrapped with `sqlalchemy.text()`. The raw-string call raises
`ObjectNotExecutableError` (a subclass of `ArgumentError`), which the
health check's broad `except Exception` swallows, so `/health` reports
postgres as "unhealthy" even when the database is fully reachable.

These tests reproduce the failure directly against SQLAlchemy's engine
(no live Postgres needed, since the error is raised before a query is
ever sent to the database) and confirm that wrapping the string in
`text()` is what fixes it.
"""

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError, ObjectNotExecutableError
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
def test_raw_string_execute_reproduces_issue_154() -> None:
    """Mirrors api/routes/health.py:31 — passing a raw string to execute()."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        with pytest.raises(ObjectNotExecutableError) as exc_info:
            conn.execute("SELECT 1")

        assert isinstance(exc_info.value, ArgumentError)


@pytest.mark.unit
def test_text_wrapped_query_succeeds() -> None:
    """Confirms `text("SELECT 1")` is the fix for the raw-string call above."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.unit
class TestHealthCheckPostgresProbe:
    """Route-level regression tests for the fixed `health_check()` postgres probe.

    These call `health_check()` directly with a mocked `AsyncSession`, the
    same pattern used in `tests/unit/test_review_service.py`. The Redis probe
    (api/routes/health.py:44-46) has a separate, pre-existing bug — it reads
    `settings.redis_host`/`redis_port`, which don't exist on `Settings` — so
    `health_status["status"]` is always "unhealthy" regardless of postgres.
    That's out of scope for #154 (see PLAN.md), so these tests read the
    per-dependency `postgres` key rather than the overall status/HTTP code.
    """

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @staticmethod
    async def _health_status(db: AsyncMock) -> Any:
        """Return health_status, whether returned directly or raised as HTTPException.detail.

        Typed `Any` rather than `dict` because `health_check()` itself is
        unannotated (pre-existing, out of scope for #154) — mypy infers its
        return as `Any`, so matching that here avoids false no-any-return /
        indexing errors on an artificially narrower type.
        """
        try:
            return await health_check(db=db)
        except HTTPException as exc:
            return exc.detail

    @pytest.mark.asyncio
    async def test_postgres_probe_executes_text_wrapped_query(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Regression test for #154: execute() must receive a text() construct, not a raw string.

        Against the pre-fix code (`db.execute("SELECT 1")`), the argument
        passed to a mocked `execute()` would be a plain `str`, not a
        `TextClause` — this assertion fails against that code and passes
        against the fix.
        """
        await self._health_status(mock_db_session)

        executed_query = mock_db_session.execute.call_args[0][0]
        assert isinstance(executed_query, TextClause)
        assert str(executed_query) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_postgres_reports_healthy_when_query_succeeds(
        self, mock_db_session: AsyncMock
    ) -> None:
        """When the DB is reachable, dependencies.postgres resolves to 'healthy'."""
        health_status = await self._health_status(mock_db_session)
        assert health_status["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_postgres_reports_unhealthy_when_connection_fails(
        self, mock_db_session: AsyncMock
    ) -> None:
        """A real connection failure (DB down) still resolves to 'unhealthy'."""
        mock_db_session.execute.side_effect = ConnectionRefusedError("connection refused")

        health_status = await self._health_status(mock_db_session)
        assert health_status["dependencies"]["postgres"] == "unhealthy"
