"""Smoke test for the Redis testcontainer wiring itself.

Isolated from any review/lock logic on purpose: if this fails, the problem
is the container/async-client setup in tests/conftest.py, not process_review().
"""

import pytest

from core.redis_client import redis_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_container_is_reachable():
    assert await redis_client.ping() is True
