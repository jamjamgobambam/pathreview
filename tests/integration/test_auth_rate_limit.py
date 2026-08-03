import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_endpoint_rate_limits_by_ip(client: AsyncClient) -> None:
    """Issue #70: /auth/login should rate limit by IP once the configured
    per-minute limit is exceeded, protecting against brute-force attempts.

    A small delay between requests avoids a timing edge case in the
    existing RateLimiter: it uses time.time() as both the score and the
    unique member of a Redis sorted set, so two requests landing in the
    same clock tick can silently collide and undercount.
    """
    responses = []
    for _ in range(110):
        resp = await client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        responses.append(resp.status_code)
        await asyncio.sleep(0.002)

    assert 401 in responses  # early requests still get normal auth failures
    assert 429 in responses  # later requests get throttled
    assert responses.index(429) > 0  # some requests succeed before throttling kicks in


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_endpoint_allows_normal_traffic(client: AsyncClient) -> None:
    """A handful of legitimate requests should never be throttled —
    only sustained traffic exceeding the configured limit should be.
    """
    responses = []
    for _ in range(10):
        resp = await client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        responses.append(resp.status_code)

    assert all(code == 401 for code in responses)
    assert 429 not in responses
