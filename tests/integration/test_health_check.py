"""Regression test for issue #154.

api/routes/health.py:31 used to run the Postgres probe as
``await db.execute("SELECT 1")`` — a bare string. SQLAlchemy 2.x rejects
bare strings for textual SQL (they must be wrapped in ``sqlalchemy.text()``),
so the probe raised ``ArgumentError``. That exception was swallowed by the
surrounding try/except, which then reported "postgres": "unhealthy" even
though the database connection itself was perfectly fine.

The fix wraps the query in ``sqlalchemy.text("SELECT 1")``. This test proves
the Postgres leg now accurately reports "healthy" against a live, working
session.

Note: the overall response still comes back as a 503 in this test because of
a separate, unrelated bug — the Redis probe references
``settings.redis_host``/``settings.redis_port``, which don't exist on
``Settings`` (see `core/config.py`), so the Redis leg always raises
``AttributeError``. That's out of scope for #154 and tracked separately; the
assertions below target the Postgres leg specifically.
"""

import pytest
import structlog
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.routes.health import health_check


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_probe_reports_healthy_for_working_connection():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=db)

    # Fixed: the probe now wraps the query in text(), so it executes
    # successfully against a working session and reports "healthy". The
    # overall status is still "unhealthy" (503) here only because of the
    # separate, unrelated Redis config bug noted above.
    assert exc_info.value.detail["dependencies"]["postgres"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_probe_logs_no_failure_event():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    with structlog.testing.capture_logs() as captured_logs:
        async with session_factory() as db:
            with pytest.raises(HTTPException):
                await health_check(db=db)

    # A regression back to a bare string would raise ArgumentError inside
    # the Postgres try/except and log "postgres_health_check_failed". This
    # asserts that event is absent, so a future regression is caught even if
    # the "healthy"/"unhealthy" string check above is ever loosened.
    postgres_failure_events = [
        entry for entry in captured_logs if entry.get("event") == "postgres_health_check_failed"
    ]
    assert postgres_failure_events == []
