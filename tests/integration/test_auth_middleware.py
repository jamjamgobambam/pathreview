"""Integration tests for the JWT auth middleware (`get_current_user`).

Each test drives a real HTTP request at a protected endpoint (`GET /reviews`)
through the app, so both layers of the authentication stack are exercised
together against the test database:

  1. ``OAuth2PasswordBearer`` parses the ``Authorization`` header. A missing
     header or a non-Bearer scheme is rejected here -- with detail
     "Not authenticated" -- before ``get_current_user`` ever runs.
  2. ``get_current_user`` decodes and validates the bearer token. Expired,
     forged, malformed, or empty tokens decode to ``None`` and are rejected
     with detail "Invalid authentication credentials". Note this layer also
     catches an empty token: OAuth2PasswordBearer checks only the scheme, not
     that a token value is present.

Every unauthorized case must return 401; the suite also asserts *which* layer
rejected the request (via the detail message), since that is what distinguishes
a header-parsing failure from a token-validation failure.
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from jose import jwt

from core.config import settings
from core.security import create_access_token

# A syntactically valid user id that need not exist in the DB: every negative
# case below is rejected at header parsing or token decoding, before the
# middleware ever looks a user up.
FAKE_USER_ID = "00000000-0000-0000-0000-000000000001"

# Protected route guarded by get_current_user with no required path/query args,
# so a rejected request yields a clean 401 rather than a 422 validation error.
PROTECTED_URL = "/reviews"


@pytest.mark.integration
class TestAuthMiddleware:
    """Unauthorized requests to a protected route must be rejected with 401."""

    # --- Layer 2: the header is well-formed but the token fails validation ---

    @pytest.mark.asyncio
    async def test_expired_token_is_rejected(self, client: AsyncClient) -> None:
        """Case 1: a token whose exp is in the past is refused at decode time.

        jose rejects the expired signature before the payload is returned, so
        this surfaces as the generic credentials error rather than a dedicated
        "expired" message.
        """
        token = create_access_token({"sub": FAKE_USER_ID}, expires_delta=timedelta(minutes=-5))
        resp = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_token_signed_with_wrong_secret_is_rejected(self, client: AsyncClient) -> None:
        """Case 2: a well-formed token signed with a different secret fails the signature check."""
        forged = jwt.encode(
            {"sub": FAKE_USER_ID},
            "a-different-secret-than-the-server-uses",
            algorithm=settings.jwt_algorithm,
        )
        resp = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {forged}"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "bad_token",
        ["this-is-not-a-jwt", "only.two", "a.b.c.d"],
        ids=["random-string", "too-few-segments", "too-many-segments"],
    )
    async def test_malformed_jwt_is_rejected(self, client: AsyncClient, bad_token: str) -> None:
        """Case 3: a random string or a wrong segment count cannot be decoded."""
        resp = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {bad_token}"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_bearer_with_extra_args_is_rejected(self, client: AsyncClient) -> None:
        """Case 7: 'Bearer a b' keeps 'a b' as the token, which then fails to decode.

        Starlette splits the header only on the first space, so the extra
        argument does not trip the OAuth2 layer; rejection happens one layer
        deeper, at token decoding.
        """
        resp = await client.get(PROTECTED_URL, headers={"Authorization": "Bearer a b"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("header", ["Bearer", "Bearer "], ids=["no-space", "trailing-space"])
    async def test_bearer_without_token_is_rejected(self, client: AsyncClient, header: str) -> None:
        """Case 5: a Bearer scheme with an empty token passes header parsing, then fails to decode.

        OAuth2PasswordBearer validates only the *scheme*, not that a token
        value is present -- so the empty token reaches get_current_user and is
        rejected at the decode layer, not at the header layer.
        """
        resp = await client.get(PROTECTED_URL, headers={"Authorization": header})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid authentication credentials"

    # --- Layer 1: the header itself is missing or has a non-Bearer scheme ---

    @pytest.mark.asyncio
    async def test_missing_authorization_header_is_rejected(self, client: AsyncClient) -> None:
        """Case 4: no Authorization header at all -> rejected before the token layer."""
        resp = await client.get(PROTECTED_URL)
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_token_without_bearer_prefix_is_rejected(self, client: AsyncClient) -> None:
        """Case 6: a valid token sent without the 'Bearer' scheme is still rejected."""
        token = create_access_token({"sub": FAKE_USER_ID})
        resp = await client.get(PROTECTED_URL, headers={"Authorization": token})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not authenticated"

    # --- Positive control: a valid token for a real, active user is accepted ---

    @pytest.mark.asyncio
    async def test_valid_token_is_accepted(self, client: AsyncClient, test_user: dict) -> None:
        """A correctly signed token for an existing, active user passes the middleware.

        Proves the 401s above come from the auth checks under test and not from a
        broken request path.
        """
        token = create_access_token({"sub": test_user["id"]})
        resp = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
