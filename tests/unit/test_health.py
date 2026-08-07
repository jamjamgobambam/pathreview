"""Tests for api/routes/health.py"""

import pytest
from unittest.mock import AsyncMock

from fastapi import HTTPException
from sqlalchemy import text

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the /health endpoint handler."""

    @pytest.mark.asyncio
    async def test_postgres_probe_uses_text_clause(self):
        """
        Regression test for issue #154.

        The PostgreSQL liveness probe must pass a SQLAlchemy ``text()`` clause,
        not a raw string. Under SQLAlchemy 2.x a raw string raises
        ``ArgumentError``, which the handler swallows and then reports postgres
        as "unhealthy" even when the database is reachable.
        """
        mock_db = AsyncMock()

        try:
            await health_check(db=mock_db)
        except HTTPException:
            # Other dependencies (e.g. redis, issue #155) may still mark the
            # overall status unhealthy and raise 503 — not relevant here.
            pass

        # The probe must have been awaited exactly once...
        mock_db.execute.assert_awaited_once()

        # ...and the statement passed must be a text() clause, not a raw string.
        statement = mock_db.execute.await_args.args[0]
        assert isinstance(statement, type(text(""))), (
            "health check DB probe must use text(), got "
            f"{type(statement).__name__}"
        )
