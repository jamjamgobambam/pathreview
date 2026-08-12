"""Integration tests for the auth routes (``/auth/register`` and ``/auth/login``).

These exercise the token *issuance* side of authentication over real HTTP
against the test database -- the complement to ``test_auth_middleware.py``,
which covers token *consumption*. Registration and login hand back a JWT on
success; the failure paths must return the right status without revealing which
half of the credentials was wrong.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User
from core.security import hash_password

# Comfortably above the UserCreate 8-char minimum so a rejection can only come
# from the behaviour under test, never from schema validation.
VALID_PASSWORD = "correct horse battery staple"


@pytest.mark.integration
class TestRegister:
    """POST /auth/register issues a token for new users and rejects duplicates."""

    @pytest.mark.asyncio
    async def test_register_new_user_returns_token(self, client: AsyncClient) -> None:
        """A brand-new email registers successfully and receives a bearer token."""
        resp = await client.post(
            "/auth/register",
            json={"email": "new-user@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]  # a non-empty JWT was issued

    @pytest.mark.asyncio
    async def test_register_duplicate_email_is_rejected(
        self, client: AsyncClient, test_user: dict
    ) -> None:
        """Re-registering an existing email is refused with 400, not a 500 or a duplicate row."""
        resp = await client.post(
            "/auth/register",
            json={"email": test_user["email"], "password": VALID_PASSWORD},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_register_short_password_is_rejected(self, client: AsyncClient) -> None:
        """A password under the 8-char minimum fails schema validation (422) before the DB."""
        resp = await client.post(
            "/auth/register",
            json={"email": "short-pw@example.com", "password": "short"},
        )
        assert resp.status_code == 422


@pytest.mark.integration
class TestLogin:
    """POST /auth/login authenticates form credentials and issues a token."""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials_returns_token(
        self, client: AsyncClient, test_user: dict
    ) -> None:
        """Correct email + password for an active user returns a bearer token."""
        resp = await client.post(
            "/auth/login",
            data={"username": test_user["email"], "password": test_user["password"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]

    @pytest.mark.asyncio
    async def test_login_with_wrong_password_is_rejected(
        self, client: AsyncClient, test_user: dict
    ) -> None:
        """A wrong password for a real user is refused with the generic credentials error."""
        resp = await client.post(
            "/auth/login",
            data={"username": test_user["email"], "password": "not-the-right-password"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_login_with_unknown_email_is_rejected(self, client: AsyncClient) -> None:
        """An unknown email returns the SAME generic error as a wrong password.

        This is the no-user-enumeration guarantee: a caller cannot tell whether
        the email exists from the response.
        """
        resp = await client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "irrelevant"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_login_inactive_user_is_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """An inactive account is refused even when the password is correct."""
        email = "inactive@example.com"
        db_session.add(
            User(email=email, hashed_password=hash_password(VALID_PASSWORD), is_active=False)
        )
        await db_session.commit()

        resp = await client.post(
            "/auth/login",
            data={"username": email, "password": VALID_PASSWORD},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "User account is inactive"
