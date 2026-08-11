"""Tests for api/routes/health.py

Covers the SQLAlchemy 2.x fix for issue #154: the PostgreSQL probe must wrap
its SQL in sqlalchemy.text() rather than passing a bare string to execute().
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy import TextClause


@pytest.mark.unit
class TestHealthCheckPostgresProbe:
    """Tests for the PostgreSQL connectivity probe in health_check()."""

    @pytest.fixture
    def mock_db(self):
        """Mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_settings(self):
        """Mock settings to avoid real Redis/VectorDB config."""
        settings = MagicMock()
        settings.redis_host = "localhost"
        settings.redis_port = 6379
        settings.vector_db_url = None
        return settings

    # ── Core fix: text() wrapper ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_postgres_probe_uses_sqlalchemy_text(self, mock_db, mock_settings):
        """
        The DB probe must pass a TextClause to execute(), not a raw string.

        SQLAlchemy 2.x raises ArgumentError when execute() receives a bare
        string: 'Textual SQL expression should be explicitly declared as
        text(...)'. This test verifies the fix wraps the probe in text().
        """
        from api.routes.health import health_check

        with patch("core.config.settings", mock_settings):
            with patch("redis.Redis") as mock_redis_cls:
                mock_redis_cls.return_value.ping.side_effect = Exception("no redis")
                try:
                    await health_check(db=mock_db)
                except HTTPException:
                    pass  # redis failure causes 503 — we only care about execute() call

        mock_db.execute.assert_called_once()
        call_arg = mock_db.execute.call_args[0][0]
        assert isinstance(call_arg, TextClause), (
            "db.execute() must receive a TextClause from sqlalchemy.text(), "
            "not a raw string. SQLAlchemy 2.x rejects bare strings with "
            "ArgumentError."
        )

    # ── Postgres healthy path ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_postgres_healthy_when_execute_succeeds(self, mock_db, mock_settings):
        """
        When db.execute() completes without error, postgres status is 'healthy'.
        """
        from api.routes.health import health_check

        with patch("core.config.settings", mock_settings):
            with patch("redis.Redis") as mock_redis_cls:
                # Redis fails so we get a 503, but postgres should still be healthy
                mock_redis_cls.return_value.ping.side_effect = Exception("no redis")
                with pytest.raises(HTTPException) as exc_info:
                    await health_check(db=mock_db)

        assert exc_info.value.detail["dependencies"]["postgres"] == "healthy"

    # ── Postgres unhealthy path ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_postgres_unhealthy_when_execute_raises(self, mock_db, mock_settings):
        """
        When db.execute() raises, postgres status is 'unhealthy' and the
        endpoint returns 503 Service Unavailable.
        """
        from api.routes.health import health_check

        mock_db.execute = AsyncMock(side_effect=Exception("connection refused"))

        with patch("core.config.settings", mock_settings):
            with patch("redis.Redis") as mock_redis_cls:
                mock_redis_cls.return_value.ping.side_effect = Exception("no redis")
                with pytest.raises(HTTPException) as exc_info:
                    await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
        assert exc_info.value.detail["status"] == "unhealthy"

    # ── Status field propagation ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_postgres_failure_sets_overall_status_unhealthy(
        self, mock_db, mock_settings
    ):
        """
        A postgres probe failure must set top-level status to 'unhealthy'.
        """
        from api.routes.health import health_check

        mock_db.execute = AsyncMock(side_effect=Exception("timeout"))

        with patch("core.config.settings", mock_settings):
            with patch("redis.Redis") as mock_redis_cls:
                mock_redis_cls.return_value.ping.side_effect = Exception("no redis")
                with pytest.raises(HTTPException) as exc_info:
                    await health_check(db=mock_db)

        assert exc_info.value.detail["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_postgres_execute_called_exactly_once(self, mock_db, mock_settings):
        """
        The health check should probe postgres exactly once per request.
        """
        from api.routes.health import health_check

        with patch("core.config.settings", mock_settings):
            with patch("redis.Redis") as mock_redis_cls:
                mock_redis_cls.return_value.ping.side_effect = Exception("no redis")
                try:
                    await health_check(db=mock_db)
                except HTTPException:
                    pass

        assert mock_db.execute.call_count == 1
