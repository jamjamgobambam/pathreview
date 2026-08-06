"""Unit tests for the /health endpoint's dependency probes."""

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


async def _call_health_check(db: AsyncMock) -> Any:
    """
    Invoke the health_check handler and return its status payload.

    The handler raises HTTPException(503) when any dependency is unhealthy, so
    unwrap that to get at the payload either way. These tests only assert on the
    Postgres probe; Redis/vector-db state is irrelevant here.
    """
    try:
        return await health_check(db=db)
    except HTTPException as exc:
        return exc.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_postgres_probe_uses_sqlalchemy_text_clause() -> None:
    """
    Regression test for #154.

    SQLAlchemy 2.x rejects raw string SQL, so the probe must pass a `text()`
    construct rather than a plain str. Before the fix this test fails, because
    `db.execute` received the string "SELECT 1".
    """
    db = AsyncMock()

    await _call_health_check(db)

    db.execute.assert_awaited_once()
    statement = db.execute.await_args.args[0]
    assert isinstance(
        statement, TextClause
    ), f"health probe must pass a SQLAlchemy text() clause, got {type(statement).__name__}"
    assert str(statement) == "SELECT 1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_postgres_reported_healthy_when_query_succeeds() -> None:
    """A working database connection should be reported as healthy."""
    db = AsyncMock()

    payload = await _call_health_check(db)

    assert payload["dependencies"]["postgres"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_postgres_reported_unhealthy_when_query_fails() -> None:
    """
    A genuinely broken database must still be reported as unhealthy — the fix
    must not mask real outages.
    """
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("connection refused")

    payload = await _call_health_check(db)

    assert payload["dependencies"]["postgres"] == "unhealthy"
    assert payload["status"] == "unhealthy"
