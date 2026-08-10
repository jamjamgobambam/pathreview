"""Tests for the health check database probe (issue #154).

SQLAlchemy 2.x requires textual SQL to be wrapped in sqlalchemy.text().
The health check route previously passed a bare string "SELECT 1" to
db.execute(), which raised ArgumentError and caused the DB probe to
always report postgres as unhealthy even when the database was reachable.

Fix: wrap the query in text("SELECT 1") so SQLAlchemy 2.x accepts it.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ArgumentError, OperationalError


class TestHealthDbProbe:
    """Tests for health check DB probe fix (issue #154)."""

    # ------------------------------------------------------------------
    # Happy path: DB is up and probe succeeds
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_postgres_reported_healthy_when_db_is_up(self) -> None:
        """DB probe returns healthy when execute(text('SELECT 1')) succeeds.

        After the fix, a working database causes the health check to report
        postgres as 'healthy' and return HTTP 200.
        """
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock()

        from api.routes.health import health_check

        # Patch Redis and vector-DB checks so only the postgres probe runs
        with (
            patch("redis.Redis") as mock_redis_cls,
            patch("core.config.settings") as mock_settings,
        ):
            mock_redis_cls.return_value.ping.return_value = True
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://localhost:8000"
            result = await health_check(db=mock_db)

        assert result["dependencies"]["postgres"] == "healthy"
        # status is only "healthy" when ALL probes pass; here we only assert
        # that the postgres key itself is correct — the focus of this fix.

    @pytest.mark.asyncio
    async def test_probe_uses_text_wrapper_not_bare_string(self) -> None:
        """The fixed code passes text('SELECT 1'), not a bare string.

        Verifies the fix is in place: the argument passed to db.execute()
        must be a SQLAlchemy TextClause, not a plain Python str.
        """
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock()

        from api.routes.health import health_check

        with (
            patch("redis.Redis") as mock_redis_cls,
            patch("core.config.settings") as mock_settings,
        ):
            mock_redis_cls.return_value.ping.return_value = True
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://localhost:8000"
            await health_check(db=mock_db)

        call_arg = mock_db.execute.call_args[0][0]
        assert not isinstance(call_arg, str), (
            "health_check must pass text('SELECT 1'), not a bare string — "
            "bare strings are rejected by SQLAlchemy 2.x (issue #154)"
        )
        # The argument should be a SQLAlchemy TextClause
        expected = text("SELECT 1")
        assert str(call_arg) == str(expected)

    # ------------------------------------------------------------------
    # Regression: SQLAlchemy 2.x ArgumentError (the original bug)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_argument_error_marks_postgres_unhealthy(self) -> None:
        """ArgumentError from a bare string causes postgres to show unhealthy.

        This is the original bug from issue #154. If the bare string were still
        used, SQLAlchemy 2.x would raise ArgumentError and the route would
        catch it, marking postgres as unhealthy and returning HTTP 503.
        We keep this test as a regression guard.
        """
        mock_db = AsyncMock()
        mock_db.execute.side_effect = ArgumentError(
            "Textual SQL expression 'SELECT 1' should be explicitly declared "
            "as text('SELECT 1')"
        )

        from fastapi import HTTPException

        from api.routes.health import health_check

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_db_genuinely_down_still_reports_unhealthy(self) -> None:
        """OperationalError (DB truly unreachable) still reports postgres as unhealthy.

        After the fix, if the database is genuinely down, db.execute() raises
        OperationalError. The except block must still catch this and report
        postgres as unhealthy — the fix must not suppress real failures.
        """
        mock_db = AsyncMock()
        mock_db.execute.side_effect = OperationalError(
            "could not connect to server", params=None, orig=None
        )

        from fastapi import HTTPException

        from api.routes.health import health_check

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_response_contains_required_keys(self) -> None:
        """Health response always includes status, dependencies, and timestamp keys."""
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock()

        from api.routes.health import health_check

        with (
            patch("redis.Redis") as mock_redis_cls,
            patch("core.config.settings") as mock_settings,
        ):
            mock_redis_cls.return_value.ping.return_value = True
            mock_settings.redis_host = "localhost"
            mock_settings.redis_port = 6379
            mock_settings.vector_db_url = "http://localhost:8000"
            result = await health_check(db=mock_db)

        assert "status" in result
        assert "dependencies" in result
        assert "timestamp" in result
        assert "postgres" in result["dependencies"]

    @pytest.mark.asyncio
    async def test_only_postgres_failure_triggers_503(self) -> None:
        """HTTP 503 is raised only when at least one dependency is unhealthy."""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = OperationalError(
            "connection refused", params=None, orig=None
        )

        from fastapi import HTTPException

        from api.routes.health import health_check

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
