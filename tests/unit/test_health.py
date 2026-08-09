"""Tests for the /health route DB probe (api/routes/health.py).

Regression tests for issue #154:
https://github.com/ascherj/pathreview/issues/154

Background: the health check probed Postgres with ``await db.execute("SELECT 1")``,
passing a bare Python string. Under SQLAlchemy 2.x a raw string is no longer an
executable object — it must be wrapped in ``sqlalchemy.text()`` — so the call
raised ``sqlalchemy.exc.ArgumentError``. The route's ``try/except`` swallowed that
error and misreported Postgres as "unhealthy" even when the database was up.

The fix wraps the query in ``text("SELECT 1")``. These tests confirm the fix by
asserting on the ``postgres`` dependency specifically: it now reports "healthy"
when the probe query succeeds, and still reports "unhealthy" on a genuine DB
error (the fix does not mask real outages).

Scope note: these tests intentionally assert on ``dependencies["postgres"]`` only.
The endpoint may still return HTTP 503 because of an unrelated, pre-existing issue
in the redis probe (it reads ``settings.redis_host`` / ``settings.redis_port``,
which are not defined on ``Settings``). That is out of scope for issue #154.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheckPostgresProbe:
    """Verify the health check's Postgres probe after the #154 fix."""

    @pytest.mark.asyncio
    async def test_health_check_reports_postgres_healthy_when_query_succeeds(self):
        """Confirms the #154 fix: Postgres reports "healthy" when the probe runs.

        With the query wrapped in ``text("SELECT 1")``, ``db.execute`` succeeds and
        the Postgres probe reports "healthy" — where the raw string previously
        raised ``ArgumentError`` and got misreported as "unhealthy".
        """
        db = AsyncMock()
        db.execute = AsyncMock()

        # The endpoint raises 503 due to the unrelated redis probe issue (see the
        # module docstring); we assert on the postgres dependency value only.
        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=db)

        detail = exc_info.value.detail
        assert detail["dependencies"]["postgres"] == "healthy"

        # Guard against a regression to a raw SQL string: the statement passed to
        # execute() must be a SQLAlchemy text() clause, not a plain str (#154).
        executed_stmt = db.execute.call_args[0][0]
        assert not isinstance(executed_stmt, str)
        assert str(executed_stmt) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_health_check_reports_postgres_unhealthy_on_real_db_error(self):
        """The fix must not mask genuine outages (#154).

        When ``db.execute`` fails with a real connectivity error (not an API
        misuse), the probe should still report Postgres "unhealthy" and the
        endpoint should return HTTP 503.
        """
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=ConnectionError("could not connect to postgres"))

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=db)

        detail = exc_info.value.detail
        assert exc_info.value.status_code == 503
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"
