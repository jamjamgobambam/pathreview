"""Integration test reproducing issue #163: review creation does not verify
profile ownership.

Reproduction steps (from the issue):
1. Register User A and User B.
2. User B creates a profile.
3. User A requests a review against User B's profile_id.

Expected: rejected with 403/404, since the profile does not belong to User A.
Actual (bug): the request succeeds and a review is created against User B's
profile.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


async def _register_user(client: AsyncClient) -> str:
    """Register a new user and return their access token."""
    email = f"user-{uuid4()}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["access_token"])


async def _create_profile(client: AsyncClient, token: str) -> str:
    """Create a profile for the given user and return its profile_id."""
    response = await client.post(
        "/profiles",
        headers={"Authorization": f"Bearer {token}"},
        data={},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_review_rejects_request_for_another_users_profile() -> None:
    """A user must not be able to create a review against another user's profile."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a = await _register_user(client)
        token_b = await _register_user(client)

        profile_b_id = await _create_profile(client, token_b)

        response = await client.post(
            "/reviews",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"profile_id": profile_b_id},
        )

        assert response.status_code in (403, 404), (
            "Expected review creation to be rejected for a profile that does "
            f"not belong to the requesting user, got {response.status_code}: "
            f"{response.text}"
        )
