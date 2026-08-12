"""Integration-test fixtures: a real (async) database connection + HTTP client.

Strategy: tests run against a DEDICATED `pathreview_test` database,
never the dev database, so integration tests can create/insert/drop freely
without touching development data. Tables are created before each test and
dropped afterwards; the FastAPI `get_db` dependency is overridden so real HTTP
requests through the app hit this test database.

Works both locally (Postgres on :5433, asyncpg URL from .env) and in CI
(Postgres service on :5432, plain postgresql:// URL) -- the URL is normalized
to the async driver and pointed at the test database regardless.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import core.models  # noqa: F401 -- imported for the side effect of registering all tables
from api.main import app
from core.config import settings
from core.database import get_db
from core.models import Base, User
from core.security import hash_password

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncEngine

TEST_DB_NAME = "pathreview_test"


def _test_db_url() -> str:
    """Derive the test-database URL from settings, forcing async driver + test DB."""
    url = make_url(settings.database_url)
    # Force the async driver (CI supplies a plain postgresql:// URL).
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")
    # Never run against the dev database.
    return str(url.set(database=TEST_DB_NAME).render_as_string(hide_password=False))


TEST_DB_URL = _test_db_url()


@pytest.fixture(scope="session")
def _ensure_test_database() -> None:
    """Create the pathreview_test database if it does not already exist.

    Uses a one-shot asyncpg connection (its own loop via asyncio.run) so it does
    not interfere with pytest-asyncio's per-test event loop.
    """

    url = make_url(TEST_DB_URL)

    async def _create_if_missing() -> None:
        conn_kwargs = {
            "host": url.host,
            "port": url.port,
            "user": url.username,
            "password": url.password,
        }
        try:
            # If we can connect to the test DB, it already exists (the CI case).
            conn = await asyncpg.connect(database=TEST_DB_NAME, **conn_kwargs)
            await conn.close()
            return
        except asyncpg.InvalidCatalogNameError:
            pass  # test DB missing -> create it below

        # Connect to the always-present maintenance DB to issue CREATE DATABASE.
        admin = await asyncpg.connect(database="postgres", **conn_kwargs)
        try:
            await admin.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
        except asyncpg.DuplicateDatabaseError:
            pass  # created concurrently; fine
        finally:
            await admin.close()

    asyncio.run(_create_if_missing())


@pytest_asyncio.fixture
async def db_engine(_ensure_test_database: None) -> AsyncGenerator[AsyncEngine, None]:
    """A fresh async engine per test, with all tables created then dropped.

    NullPool avoids connections being reused across pytest-asyncio's per-test
    event loops (a common source of 'attached to a different loop' errors).
    """
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """An AsyncSession bound to the test database, for direct DB setup/asserts."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient wired to the app, with get_db pointed at the test DB.

    This is the crucial link: overriding get_db means every real HTTP request the
    test makes resolves its database session against pathreview_test.
    """
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Insert a known active user directly into the test DB.

    Returns the plaintext credentials so login/flow tests can authenticate.
    """
    email = "test-user@example.com"
    password = "correct horse battery staple"
    user = User(email=email, hashed_password=hash_password(password), is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {"id": str(user.id), "email": email, "password": password}
