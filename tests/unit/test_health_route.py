"""Reproduction test for issue #155.

The /health endpoint's Redis probe builds its client with
``redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)``, but
``core.config.Settings`` only defines a single ``redis_url`` field — it has
neither ``redis_host`` nor ``redis_port``. Evaluating ``settings.redis_host``
therefore raises ``AttributeError``, which the route's surrounding try/except
swallows and records Redis as ``"unhealthy"``, forcing the endpoint to return
HTTP 503 even when Redis is actually reachable.

This test simulates a reachable Redis (``ping()`` succeeds) and asserts the
probe reports ``"healthy"``. It currently fails because of the attribute
mismatch, so it is marked ``xfail`` to document the reproduction without
breaking CI. When issue #155 is fixed (Week 9), remove the ``xfail`` marker;
``strict=True`` makes the now-passing test surface as XPASS to remind us to
do so.

Ref: https://github.com/ascherj/pathreview/issues/155
"""

from unittest.mock import AsyncMock, patch

import pytest

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason="Issue #155: health route reads settings.redis_host / redis_port, "
    "which do not exist on Settings (only redis_url). Remove marker when fixed.",
)
@patch("redis.Redis")
async def test_health_reports_redis_healthy_when_ping_succeeds(mock_redis: object) -> None:
    """With Redis reachable, the /health Redis probe should report 'healthy'.

    The patch covers both plausible client-construction styles so this test
    stays valid regardless of how the fix is written:
      - ``redis.Redis(...)``            (current, buggy)
      - ``redis.Redis.from_url(...)``   (preferred fix, uses settings.redis_url)
    """
    # Simulate a reachable Redis: the client's ping() succeeds.
    mock_redis.return_value.ping.return_value = True
    mock_redis.from_url.return_value.ping.return_value = True

    # Mock the DB dependency so the Postgres probe passes and we isolate Redis.
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    result = await health_check(db=mock_db)

    assert result["dependencies"]["redis"] == "healthy"
    assert result["status"] == "healthy"
