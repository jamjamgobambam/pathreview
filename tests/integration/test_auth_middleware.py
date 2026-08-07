"""Integration tests for authentication middleware rejection paths."""

import base64
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

import pytest
from httpx import AsyncClient
from jose import jwt

from core.config import settings
from core.security import create_access_token


def _future_exp() -> datetime:
    """Return expiry five minutes from now."""
    return datetime.now(UTC) + timedelta(minutes=5)


def _b64(segment: dict[str, object]) -> str:
    """Base64url-encode one JWT segment without padding."""
    return base64.urlsafe_b64encode(json.dumps(segment).encode()).rstrip(b"=").decode()


def _token_signed_with_foreign_secret() -> str:
    """A structurally valid, unexpired JWT signed with a secret the app does not know."""
    return cast(
        "str",
        jwt.encode({"sub": "someone", "exp": _future_exp()}, "wrong-secret", algorithm="HS256"),
    )


def _token_with_unwhitelisted_algorithm() -> str:
    """A JWT signed with the app's REAL secret but an algorithm outside the whitelist."""
    return cast(
        "str",
        jwt.encode(
            {"sub": "someone", "exp": _future_exp()}, settings.secret_key, algorithm="HS512"
        ),
    )


def _forged_alg_none_token() -> str:
    """The classic alg=none forgery: real-looking claims, no signature."""
    header = _b64({"alg": "none", "typ": "JWT"})
    payload = _b64({"sub": "admin", "exp": int(_future_exp().timestamp())})
    return f"{header}.{payload}."


@pytest.mark.integration
class TestAuthMiddleware:
    """Test suite for get_current_user rejection paths (issue #90)."""

    @pytest.mark.parametrize(
        "headers",
        [None, {"Authorization": "Basic YWJjOjEyMw=="}],
        ids=["no-header", "wrong-scheme"],
    )
    @pytest.mark.asyncio
    async def test_absent_credential_returns_401(
        self, async_client: AsyncClient, headers: dict[str, str] | None
    ) -> None:
        """Test absent or non-Bearer credentials return 401 'Not authenticated'."""
        response = await async_client.get("/reviews", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.parametrize(
        "bad_token",
        ["not.a.jwt", "a.b", "aaa.bbb.ccc", ""],
        ids=["not-a-jwt", "two-segments", "undecodable-base64", "empty-token"],
    )
    @pytest.mark.asyncio
    async def test_undecodable_token_returns_401(
        self, async_client: AsyncClient, bad_token: str
    ) -> None:
        """Test tokens jose cannot decode return 401 'Invalid authentication credentials'."""
        response = await async_client.get(
            "/reviews", headers={"Authorization": f"Bearer {bad_token}"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, async_client: AsyncClient) -> None:
        """Test an expired token returns the generic 401, not 'Token has expired'."""
        expired_token = create_access_token(
            {"sub": "someone"}, expires_delta=timedelta(minutes=-10)
        )
        response = await async_client.get(
            "/reviews", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.parametrize(
        "make_token",
        [
            _token_signed_with_foreign_secret,
            _token_with_unwhitelisted_algorithm,
            _forged_alg_none_token,
        ],
        ids=["foreign-secret", "hs512-not-whitelisted", "alg-none-forgery"],
    )
    @pytest.mark.asyncio
    async def test_bad_signature_or_algorithm_returns_401(
        self, async_client: AsyncClient, make_token: Callable[[], str]
    ) -> None:
        """Test cryptographically invalid tokens return 401 regardless of how they are wrong."""
        response = await async_client.get(
            "/reviews", headers={"Authorization": f"Bearer {make_token()}"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_token_without_sub_claim_returns_401(self, async_client: AsyncClient) -> None:
        """Test a valid, decodable token carrying no 'sub' claim is rejected."""
        token = create_access_token({"user_id": "123"})
        response = await async_client.get("/reviews", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_token_for_unknown_user_returns_401(self, async_client: AsyncClient) -> None:
        """Test a valid token whose subject has no row in the database is rejected."""
        token = create_access_token({"sub": str(uuid4())})
        response = await async_client.get("/reviews", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_valid_token_for_existing_user_returns_200(
        self, async_client: AsyncClient, auth_token: str
    ) -> None:
        """Test a valid token for a persisted user reaches the protected route."""
        response = await async_client.get(
            "/reviews", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["items"] == []
