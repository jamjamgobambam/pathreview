"""Integration tests for JWT authentication middleware."""

from collections.abc import Iterator
from datetime import timedelta
from typing import TypedDict, cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from jose import jwt  # type: ignore[import-untyped]

from api.main import app
from core.config import settings
from core.security import create_access_token

pytestmark = pytest.mark.integration


class RegisteredUser(TypedDict):
    """Authenticated user data created for middleware tests."""

    id: str
    token: str


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    """Provide one app client and trigger application startup once."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def registered_user(client: TestClient) -> RegisteredUser:
    """Register a real user so valid tokens can pass middleware lookup."""
    response = client.post(
        "/auth/register",
        json={
            "email": f"auth-middleware-{uuid4()}@example.com",
            "password": "secure-password-123",
        },
    )

    assert response.status_code == 200
    body = cast("dict[str, str]", response.json())
    token = body["access_token"]
    payload = jwt.get_unverified_claims(token)

    return {"id": str(payload["sub"]), "token": token}


def profile_url() -> str:
    """Return a valid-but-nonexistent profile URL."""
    return f"/profiles/{uuid4()}"


def bearer_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def assert_unauthorized(response: Response, detail: str) -> None:
    """Assert the public authentication rejection contract."""
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {"detail": detail}


class TestValidCredentials:
    """Tests that prove valid credentials pass the middleware."""

    def test_valid_token_reaches_protected_route(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """A valid token reaches the route handler instead of returning 401."""
        response = client.get(profile_url(), headers=bearer_headers(registered_user["token"]))

        assert response.status_code == 404
        assert response.json() == {"detail": "Profile not found"}


class TestMissingAuthorization:
    """Tests for absent or incorrectly formatted authorization headers."""

    def test_missing_authorization_header_is_rejected(self, client: TestClient) -> None:
        """Requests without credentials receive the OAuth2 authentication response."""
        response = client.get(profile_url())

        assert_unauthorized(response, "Not authenticated")

    def test_empty_bearer_token_is_rejected(self, client: TestClient) -> None:
        """An empty bearer token is rejected by token decoding."""
        response = client.get(profile_url(), headers={"Authorization": "Bearer "})

        assert_unauthorized(response, "Invalid authentication credentials")

    def test_wrong_scheme_is_rejected(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """A valid token cannot bypass the middleware under a non-bearer scheme."""
        response = client.get(
            profile_url(),
            headers={"Authorization": f"Basic {registered_user['token']}"},
        )

        assert_unauthorized(response, "Not authenticated")


class TestMalformedTokens:
    """Tests for invalid JWT structures and signatures."""

    @pytest.mark.parametrize("token", ["not-a-jwt", "header.payload", "a.b.c"])
    def test_malformed_token_is_rejected(self, client: TestClient, token: str) -> None:
        """Malformed token strings receive the middleware's generic 401 response."""
        response = client.get(profile_url(), headers=bearer_headers(token))

        assert_unauthorized(response, "Invalid authentication credentials")

    def test_tampered_payload_is_rejected(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """Changing a token payload invalidates its signature."""
        header, payload, signature = registered_user["token"].split(".")
        altered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
        tampered_token = f"{header}.{altered_payload}.{signature}"

        response = client.get(profile_url(), headers=bearer_headers(tampered_token))

        assert_unauthorized(response, "Invalid authentication credentials")

    def test_missing_signature_is_rejected(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """A two-part token cannot be accepted as a signed JWT."""
        unsigned_token = registered_user["token"].rsplit(".", maxsplit=1)[0]

        response = client.get(profile_url(), headers=bearer_headers(unsigned_token))

        assert_unauthorized(response, "Invalid authentication credentials")


class TestExpiredToken:
    """Tests for expiry handling in the observable middleware contract."""

    def test_expired_token_is_rejected(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """Expired credentials receive the generic invalid-token response."""
        token = create_access_token(
            {"sub": registered_user["id"]},
            expires_delta=timedelta(minutes=-5),
        )

        response = client.get(profile_url(), headers=bearer_headers(token))

        assert_unauthorized(response, "Invalid authentication credentials")


class TestWrongSecretToken:
    """Tests for JWTs signed with an untrusted secret."""

    def test_token_signed_with_wrong_secret_is_rejected(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """A token with the correct claims but wrong signature is rejected."""
        token = jwt.encode(
            {"sub": registered_user["id"]},
            "different-test-secret",
            algorithm=settings.jwt_algorithm,
        )

        response = client.get(profile_url(), headers=bearer_headers(token))

        assert_unauthorized(response, "Invalid authentication credentials")


class TestAdditionalClaims:
    """Tests for validly signed tokens that cannot identify a real user."""

    def test_token_without_subject_is_rejected(self, client: TestClient) -> None:
        """A correctly signed token must include the subject claim."""
        token = create_access_token({})

        response = client.get(profile_url(), headers=bearer_headers(token))

        assert_unauthorized(response, "Invalid authentication credentials")

    def test_token_for_unknown_user_is_rejected(self, client: TestClient) -> None:
        """A token subject must correspond to an existing user."""
        token = create_access_token({"sub": str(uuid4())})

        response = client.get(profile_url(), headers=bearer_headers(token))

        assert_unauthorized(response, "Invalid authentication credentials")

    def test_near_expiry_token_is_accepted(
        self, client: TestClient, registered_user: RegisteredUser
    ) -> None:
        """A token that remains unexpired is allowed through the middleware."""
        token = create_access_token(
            {"sub": registered_user["id"]},
            expires_delta=timedelta(seconds=30),
        )

        response = client.get(profile_url(), headers=bearer_headers(token))

        assert response.status_code == 404
        assert response.json() == {"detail": "Profile not found"}
