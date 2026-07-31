"""Shared fixtures for integration tests.

These tests exercise the real FastAPI app against a real Postgres database
(via `core.database`/`core.config.settings`) — there is no SQLite fallback
or DB mocking in this codebase, so a Postgres instance must be reachable at
`settings.database_url` before running them.

Locally:

    docker compose up -d db
    DATABASE_URL=postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_dev \
        .venv/bin/alembic upgrade head
    make test-integration

This mirrors the `postgres` service the `test-integration` job in
`.github/workflows/ci.yml` spins up for CI.
"""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from core.database import AsyncSessionLocal, engine
from core.models.user import User
from core.security import create_access_token, hash_password


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_test() -> AsyncGenerator[None, None]:
    """Dispose pooled connections after each test.

    pytest-asyncio gives each test function its own event loop by default.
    The SQLAlchemy async engine (and its asyncpg connection pool) is a
    module-level singleton, so without this a connection opened in one
    test's loop gets reused/closed against a different, already-closed
    loop in the next test, raising "Event loop is closed" during teardown.
    """
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session bound to the same engine the app uses."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """Create a persisted user for auth tests and clean it up afterwards."""
    user = User(
        email=f"auth-test-{uuid4()}@example.com",
        hashed_password=hash_password("Sup3rSecret!123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    yield user

    await db_session.delete(user)
    await db_session.commit()


@pytest_asyncio.fixture
def auth_token(test_user: User) -> str:
    """A valid JWT access token for `test_user`."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """An httpx client wired directly to the FastAPI app (no network)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
