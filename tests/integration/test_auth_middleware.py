"""Integration tests for `get_current_user()` (api/middleware/auth.py).

`get_current_user` is the single dependency guarding every protected route,
but it had only ever been exercised with a valid token. These tests cover
the previously-untested edge cases: expired tokens, malformed tokens, a
missing `Authorization` header, and tokens signed with a different secret.

All five cases below were manually reproduced against a running instance
first (see JOURNAL.md / PLAN.md) — the middleware already behaves correctly.
This file locks that behavior in so a future regression is caught by CI
instead of going unnoticed.

Tested against `GET /profiles/{profile_id}`, a real protected route, rather
than mocking the dependency directly, so the tests cover the full stack:
`OAuth2PasswordBearer` -> `decode_access_token()` -> `get_current_user()`.

Known follow-up (out of scope here, see PLAN.md): the expired-token case
returns the generic "Invalid authentication credentials" message rather
than the more specific "Token has expired" message. That's because
`decode_access_token()` already swallows `ExpiredSignatureError` (a
`JWTError` subclass) and returns `None`, so the dedicated expiry check in
`get_current_user()` is dead code. Still a correct 401, just a less
specific message -- asserted as-is below, not as it "should" be.
"""

from datetime import timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from jose import jwt

from core.config import settings
from core.models.user import User
from core.security import create_access_token

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_valid_token_passes_auth(client: AsyncClient, auth_token: str) -> None:
    """Baseline: a valid token reaches the route handler (404, not 401)."""
    response = await client.get(
        f"/profiles/{uuid4()}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"


@pytest.mark.asyncio
async def test_missing_authorization_header(client: AsyncClient) -> None:
    """No `Authorization` header at all is rejected before reaching the route."""
    response = await client.get(f"/profiles/{uuid4()}")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_malformed_token(client: AsyncClient) -> None:
    """A token that isn't valid JWT structure is rejected."""
    response = await client.get(
        f"/profiles/{uuid4()}",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_wrong_secret_token(client: AsyncClient, test_user: User) -> None:
    """A well-formed token signed with a different secret is rejected."""
    forged_token = jwt.encode(
        {"sub": str(test_user.id)},
        "a-completely-different-secret",
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        f"/profiles/{uuid4()}",
        headers={"Authorization": f"Bearer {forged_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_expired_token(client: AsyncClient, test_user: User) -> None:
    """An expired token is rejected.

    Asserts the generic message the code actually returns today (see the
    module docstring for the dead-code finding), not the more specific
    "Token has expired" message a separate branch of `get_current_user`
    appears to intend.
    """
    expired_token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(seconds=-10),
    )

    response = await client.get(
        f"/profiles/{uuid4()}",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"
