"""End-to-end integration tests for the full authentication workflow.

Where ``test_auth_routes`` checks token *issuance* and ``test_auth_middleware``
checks token *consumption* in isolation, these tests verify the two compose: a
token minted by the real ``/auth/register`` or ``/auth/login`` endpoint is
accepted by ``get_current_user`` on a protected route. This exercises the whole
chain -- ``str(user.id)`` -> ``sub`` claim -> JWT -> decode -> DB lookup -- that
the middleware suite's self-forged token deliberately does not.
"""

import pytest
from httpx import AsyncClient

# Comfortably above the UserCreate 8-char minimum.
VALID_PASSWORD = "correct horse battery staple"

# Protected route guarded by get_current_user with no required path/query args.
PROTECTED_URL = "/reviews"


@pytest.mark.integration
class TestAuthWorkflow:
    """A token from a real auth endpoint must unlock a protected route."""

    @pytest.mark.asyncio
    async def test_register_issues_token_that_grants_access(self, client: AsyncClient) -> None:
        """Registering yields a token that immediately authenticates a protected request."""
        register = await client.post(
            "/auth/register",
            json={"email": "workflow-register@example.com", "password": VALID_PASSWORD},
        )
        assert register.status_code == 200
        token = register.json()["access_token"]

        protected = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
        assert protected.status_code == 200

    @pytest.mark.asyncio
    async def test_login_issues_token_that_grants_access(
        self, client: AsyncClient, test_user: dict
    ) -> None:
        """Logging in as a pre-existing user yields a token that unlocks a protected route."""
        login = await client.post(
            "/auth/login",
            data={"username": test_user["email"], "password": test_user["password"]},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        protected = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
        assert protected.status_code == 200

    @pytest.mark.asyncio
    async def test_full_register_login_then_access(self, client: AsyncClient) -> None:
        """The complete user journey: register, then log in fresh, then use that token.

        The token discarded from registration and a new one obtained via login
        proves login works end to end for an account created earlier in the
        same flow -- not just for a fixture-seeded user.
        """
        email = "workflow-full@example.com"

        register = await client.post(
            "/auth/register",
            json={"email": email, "password": VALID_PASSWORD},
        )
        assert register.status_code == 200

        login = await client.post(
            "/auth/login",
            data={"username": email, "password": VALID_PASSWORD},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        protected = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
        assert protected.status_code == 200
