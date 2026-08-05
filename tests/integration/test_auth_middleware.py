"""Integration tests for authentication middleware edge cases.

Issue #90: The auth middleware is only tested with a valid token.
These tests document the missing coverage for:
- Expired tokens
- Malformed tokens
- Missing Authorization header
- Tokens signed with a wrong secret
"""

from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from core.security import create_access_token


@pytest.fixture
def valid_token() -> str:
    """Create a valid token for a fake user ID."""
    return create_access_token(data={"sub": "test-user-id"})


@pytest.fixture
def expired_token() -> str:
    """Create a token that is already expired."""
    return create_access_token(
        data={"sub": "test-user-id"},
        expires_delta=timedelta(seconds=-1),
    )


@pytest.fixture
def wrong_secret_token() -> str:
    """Create a token signed with a different secret key."""
    from jose import jwt

    return jwt.encode(
        {"sub": "test-user-id"},
        "completely-wrong-secret",
        algorithm="HS256",
    )


@pytest.mark.asyncio
async def test_expired_token_returns_401() -> None:
    """Expired tokens should be rejected with 401."""
    token = create_access_token(
        data={"sub": "test-user-id"},
        expires_delta=timedelta(seconds=-1),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/profiles/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_malformed_token_returns_401() -> None:
    """Garbage string tokens should be rejected with 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/profiles/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": "Bearer not.a.real.token"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_auth_header_returns_401() -> None:
    """Requests with no Authorization header should be rejected with 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/profiles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_secret_token_returns_401() -> None:
    """Tokens signed with a different secret should be rejected with 401."""
    from jose import jwt

    token = jwt.encode(
        {"sub": "test-user-id"},
        "completely-wrong-secret",
        algorithm="HS256",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/profiles/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 401
