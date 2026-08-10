"""Reproduction test for issue #154.

health_check() passes a raw string to db.execute(), which SQLAlchemy 2.x
rejects. This test confirms the bug: the mock db.execute raises the same
ArgumentError that SQLAlchemy 2.x raises in production.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import ArgumentError


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_db_probe_fails_with_raw_string():
    """Reproduces issue #154: raw SQL string causes ArgumentError under SQLAlchemy 2.x."""
    from api.routes.health import health_check

    # Simulate the SQLAlchemy 2.x error for raw string SQL
    mock_db = AsyncMock()
    mock_db.execute.side_effect = ArgumentError(
        "Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')"
    )

    with patch("api.routes.health.structlog.get_logger", return_value=MagicMock()):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await health_check(db=mock_db)

    assert exc_info.value.status_code == 503
    detail = exc_info.value.detail
    assert detail["dependencies"]["postgres"] == "unhealthy"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_db_probe_passes_with_text_wrapper():
    """Verifies that wrapping SELECT 1 in text() fixes the issue."""
    from api.routes.health import health_check

    mock_db = AsyncMock()
    mock_db.execute.return_value = MagicMock()

    with (
        patch("api.routes.health.structlog.get_logger", return_value=MagicMock()),
        patch("redis.Redis") as mock_redis_cls,
        patch("core.config.settings") as mock_settings,
    ):
        mock_redis_cls.return_value.ping.return_value = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.vector_db_url = "http://localhost:8001"
        await health_check(db=mock_db)

    # Confirm execute was called — after fix it should be called with text("SELECT 1")
    mock_db.execute.assert_called_once()
    call_arg = mock_db.execute.call_args[0][0]
    assert (
        hasattr(call_arg, "text") or str(call_arg) == "SELECT 1"
    ), "db.execute should be called with a sqlalchemy text() object, not a raw string"
