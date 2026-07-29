"""Integration tests for profile_service.py against a real PostgreSQL database.

Each test asserts a claim made by the docstrings in core/services/profile_service.py.
Requires the docker-compose `db` service to be running.

The schema is built with alembic rather than Base.metadata.create_all, because the
models declare their indexes twice (an index=True column plus a matching Index() in
__table_args__), which makes create_all emit duplicate CREATE INDEX statements.
"""

import os
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.schemas.profile import ProfileCreate
from core.models.profile import Profile
from core.models.user import User
from core.services.profile_service import create_profile, get_profile

REPO_ROOT = Path(__file__).resolve().parents[2]

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_test",
)

DATA_TABLES = "users, profiles, reviews, ingested_sources"


@pytest.fixture(scope="session")
def migrated_database() -> str:
    """Bring the test database up to head, once per session."""
    alembic_bin = Path(sys.executable).parent / "alembic"
    subprocess.run(
        [str(alembic_bin), "upgrade", "head"],
        cwd=REPO_ROOT,
        env={**os.environ, "DATABASE_URL": TEST_DATABASE_URL},
        check=True,
        capture_output=True,
    )
    return TEST_DATABASE_URL


@pytest_asyncio.fixture
async def db(migrated_database: str) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session, then clear every data table so tests cannot leak into each other."""
    engine = create_async_engine(migrated_database)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {DATA_TABLES} RESTART IDENTITY CASCADE"))
    await engine.dispose()


async def _make_user(db: AsyncSession) -> User:
    record = User(
        id=str(uuid4()),
        email=f"{uuid4()}@example.com",
        hashed_password="not-a-real-hash",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@pytest_asyncio.fixture
async def user(db: AsyncSession) -> User:
    """Persist a user to satisfy the profiles.user_id foreign key."""
    return await _make_user(db)


@pytest_asyncio.fixture
async def other_user(db: AsyncSession) -> User:
    """A second user, used to prove ownership filtering."""
    return await _make_user(db)


@pytest.mark.integration
class TestCreateProfile:
    """Verify the claims in create_profile's docstring."""

    @pytest.mark.asyncio
    async def test_row_is_actually_persisted(self, db: AsyncSession, user: User) -> None:
        """The returned Profile corresponds to a committed row, not just an object."""
        created = await create_profile(
            db, user.id, ProfileCreate(github_username="janedoe", portfolio_url=None)
        )

        found = await db.execute(select(Profile).where(Profile.id == created.id))
        assert found.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_all_five_arguments_are_stored(self, db: AsyncSession, user: User) -> None:
        """github_username, portfolio_url, resume_filename and resume_text all persist."""
        created = await create_profile(
            db,
            user.id,
            ProfileCreate(github_username="janedoe", portfolio_url="https://jane.dev"),
            resume_filename="jane.pdf",
            resume_text="Jane Doe, Software Engineer",
        )

        assert created.user_id == user.id
        assert created.github_username == "janedoe"
        assert created.portfolio_url == "https://jane.dev"
        assert created.resume_filename == "jane.pdf"
        assert created.resume_text == "Jane Doe, Software Engineer"

    @pytest.mark.asyncio
    async def test_returned_object_has_generated_fields_populated(
        self, db: AsyncSession, user: User
    ) -> None:
        """The docstring's "refreshed with database-generated fields" claim."""
        created = await create_profile(
            db, user.id, ProfileCreate(github_username=None, portfolio_url=None)
        )

        assert created.id is not None
        assert created.created_at is not None
        assert created.updated_at is not None

    @pytest.mark.asyncio
    async def test_calling_twice_creates_two_distinct_rows(
        self, db: AsyncSession, user: User
    ) -> None:
        """It inserts; it does not upsert. A user may hold multiple profiles."""
        first = await create_profile(
            db, user.id, ProfileCreate(github_username="janedoe", portfolio_url=None)
        )
        second = await create_profile(
            db, user.id, ProfileCreate(github_username="janedoe", portfolio_url=None)
        )

        assert first.id != second.id

        rows = await db.execute(select(Profile).where(Profile.user_id == user.id))
        assert len(rows.scalars().all()) == 2


@pytest.mark.integration
class TestGetProfile:
    """Verify the claims in get_profile's docstring."""

    @pytest.mark.asyncio
    async def test_returns_profile_for_its_owner(self, db: AsyncSession, user: User) -> None:
        created = await create_profile(
            db, user.id, ProfileCreate(github_username="janedoe", portfolio_url=None)
        )

        found = await get_profile(db, created.id, user.id)

        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_returns_none_when_owned_by_another_user(
        self, db: AsyncSession, user: User, other_user: User
    ) -> None:
        """The row exists, but the requester does not own it -> None."""
        created = await create_profile(
            db, user.id, ProfileCreate(github_username="janedoe", portfolio_url=None)
        )

        found = await get_profile(db, created.id, other_user.id)

        assert found is None

    @pytest.mark.asyncio
    async def test_returns_none_when_profile_does_not_exist(
        self, db: AsyncSession, user: User
    ) -> None:
        """A never-created ID is indistinguishable from one owned by someone else."""
        found = await get_profile(db, str(uuid4()), user.id)

        assert found is None
