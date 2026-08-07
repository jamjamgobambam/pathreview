from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from api.main import app
from core.database import AsyncSessionLocal, engine
from core.models import User
from core.security import create_access_token


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Return an httpx AsyncClient wired to the app for DB-backed tests."""
    await engine.dispose()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user() -> AsyncGenerator[User, None]:
    """Persist a real user for the duration of one test, then remove it."""
    await engine.dispose()
    user = User(
        id=str(uuid4()),
        email=f"auth-test-{uuid4()}@example.com",
        hashed_password="not-a-real-hash",
        is_active=True,
    )
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
    try:
        yield user
    finally:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest_asyncio.fixture
async def auth_token(test_user: User) -> str:
    """Return a valid JWT for the persisted test user."""
    return create_access_token({"sub": test_user.id})
