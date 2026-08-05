"""Tests for the /health endpoint (api/routes/health.py).

Issue #154: the PostgreSQL liveness probe passed a bare string to
``AsyncSession.execute``. Under SQLAlchemy 2.x that raises ``ArgumentError``
("Textual SQL expression 'SELECT 1' should be explicitly declared as
text('SELECT 1')"), which the probe's ``except`` block swallowed, so ``/health``
reported Postgres unhealthy and returned 503 even when the database was up.
The fix wraps the query in ``sqlalchemy.text()``.

These tests cover two things:

1. The 200/503 branching logic (Postgres healthy vs. probe error).
2. A regression guard that the probe is called with a ``text()`` clause and not
   a raw string. A plain ``AsyncMock`` accepts any argument, so branching tests
   alone pass whether or not the fix is present; asserting the executed argument
   is a ``TextClause`` is what actually fails if the raw-string bug returns.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.elements import TextClause

from api.routes.health import health_check


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the health_check route."""

    @pytest.fixture
    def healthy_redis(self):
        """Satisfy the Redis probe so overall status can reach 'healthy'.

        The route reads ``settings.redis_host``/``settings.redis_port`` (which do
        not exist on the real ``Settings`` — a separate, out-of-scope bug) and
        calls ``redis.Redis(...).ping()``. Swap ``settings`` for a stub and patch
        ``redis.Redis`` so the Postgres assertions are not masked by an unrelated
        dependency failure. (``patch.object`` can't add attributes to the pydantic
        ``Settings`` model, so we replace the object wholesale.)
        """
        stub_settings = SimpleNamespace(
            redis_host="localhost",
            redis_port=6379,
            vector_db_url="http://localhost:8001",
        )
        with patch("core.config.settings", stub_settings), patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            yield mock_redis

    @pytest.mark.asyncio
    async def test_reports_postgres_healthy_when_probe_succeeds(self, healthy_redis):
        """DB reachable -> 200 with dependencies.postgres == 'healthy'."""
        session = AsyncMock()
        session.execute = AsyncMock()

        result = await health_check(db=session)

        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"

    @pytest.mark.asyncio
    async def test_reports_postgres_unhealthy_when_probe_raises(self):
        """DB probe error -> HTTPException(503) with postgres == 'unhealthy'."""
        session = AsyncMock()
        session.execute = AsyncMock(side_effect=Exception("boom"))

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=session)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_probe_uses_text_clause_not_raw_string(self, healthy_redis):
        """Regression guard for #154: the probe must run a SQLAlchemy ``text()``
        clause, not a raw string, or it breaks under SQLAlchemy 2.x."""
        session = AsyncMock()
        session.execute = AsyncMock()

        await health_check(db=session)

        session.execute.assert_awaited_once()
        probe_arg = session.execute.await_args.args[0]
        assert isinstance(probe_arg, TextClause), (
            "health probe must use sqlalchemy.text('SELECT 1'), not a raw string "
            "(raw strings raise ArgumentError under SQLAlchemy 2.x — issue #154)"
        )
        assert str(probe_arg) == "SELECT 1"
