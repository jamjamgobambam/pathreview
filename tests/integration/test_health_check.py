"""Reproduction test for issue #154.

api/routes/health.py:31 runs the Postgres probe as
``await db.execute("SELECT 1")`` — a bare string. SQLAlchemy 2.x rejects
bare strings for textual SQL (they must be wrapped in ``sqlalchemy.text()``),
so the probe raises ``ArgumentError``. That exception is swallowed by the
surrounding try/except, which then reports "postgres": "unhealthy" even
though the database connection itself is perfectly fine.

This test proves the false negative: against a live, working SQLite
session, the health check still reports Postgres as unhealthy.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.routes.health import health_check


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_probe_reports_unhealthy_despite_working_connection():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=db)

    # Bug: the probe's raw-string execute() raises ArgumentError, which is
    # caught and misreported as the database being down.
    assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
