"""Regression tests for issue #155.

Background: the ``/health`` endpoint's Redis probe used to build its client with
``redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)``, but
``core.config.Settings`` only defines a single ``redis_url`` field. Evaluating
``settings.redis_host`` raised ``AttributeError``, which the route's try/except
swallowed and recorded Redis as ``"unhealthy"``, forcing HTTP 503 even when Redis
was reachable.

The fix builds the client from the config that actually exists —
``redis.Redis.from_url(settings.redis_url, ...)``. These tests pin both the
happy path (reachable Redis → ``"healthy"`` → 200) and the failure path
(unreachable Redis → ``"unhealthy"`` → 503) so the probe reflects Redis's true
state and can't silently mask an outage.

Ref: https://github.com/ascherj/pathreview/issues/155
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis
from fastapi import HTTPException

from api.routes.health import health_check


@pytest.mark.unit
@pytest.mark.asyncio
@patch("redis.Redis")
async def test_health_reports_redis_healthy_when_ping_succeeds(mock_redis: MagicMock) -> None:
    """A reachable Redis (ping succeeds) is reported as 'healthy' and yields 200.

    Patches both plausible client-construction styles so the test is robust to
    how the probe is written:
      - ``redis.Redis(...)``
      - ``redis.Redis.from_url(...)``  (the fix)
    """
    mock_redis.return_value.ping.return_value = True
    mock_redis.from_url.return_value.ping.return_value = True

    # Mock the DB dependency so the Postgres probe passes and Redis is isolated.
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    result = await health_check(db=mock_db)

    assert result["dependencies"]["redis"] == "healthy"
    assert result["status"] == "healthy"


@pytest.mark.unit
@pytest.mark.asyncio
@patch("redis.Redis")
async def test_health_reports_redis_unhealthy_when_ping_fails(mock_redis: MagicMock) -> None:
    """An unreachable Redis (ping raises) is reported 'unhealthy' and yields 503."""
    mock_redis.return_value.ping.side_effect = redis.ConnectionError("connection refused")
    mock_redis.from_url.return_value.ping.side_effect = redis.ConnectionError("connection refused")

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await health_check(db=mock_db)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["dependencies"]["redis"] == "unhealthy"
