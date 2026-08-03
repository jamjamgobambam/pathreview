import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_endpoint_rate_limits_by_ip(client: AsyncClient) -> None:
    """Issue #70: /auth/login should rate limit by IP once the configured
    per-minute limit is exceeded, protecting against brute-force attempts.
    """
    responses = []
    for _ in range(110):
        resp = await client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        responses.append(resp.status_code)

    assert 401 in responses  # early requests still get normal auth failures
    assert 429 in responses  # later requests get throttled
    assert responses.index(429) > 0  # some requests succeed before throttling kicks in
