import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_endpoint_has_no_rate_limiting_yet(client: AsyncClient) -> None:
    """Reproduction test for issue #70: /auth/login has no rate limiting.
    This test documents the current (broken) behavior and should start
    failing once rate limiting is implemented — at which point it should
    be updated to assert a 429 is eventually returned.
    """
    responses = []
    for _ in range(50):
        resp = await client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpass"},
        )
        responses.append(resp.status_code)
    assert all(code == 401 for code in responses)  # every attempt fails auth...
    assert 429 not in responses  # ...but none are ever throttled — the bug
