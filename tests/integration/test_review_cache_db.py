"""Integration tests for the review cache lookup (#32).

The unit suite's session double cannot evaluate SQL, so these tests pin the
cache predicate against the real Postgres from docker compose: a hit
requires matching profile_id, matching content_hash, and status="complete",
and ties resolve to the newest matching review. Each test runs inside an
outer transaction that is rolled back, leaving the database unchanged.
"""

from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from core.config import settings
from core.models.profile import Profile
from core.models.review import Review
from core.models.user import User
from core.services.review_service import compute_content_hash, create_review


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Session bound to an outer transaction that is always rolled back.

    create_review commits its own work, so the session joins the outer
    transaction through savepoints; the rollback at the end discards
    everything a test wrote.
    """
    engine = create_async_engine(settings.database_url)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


async def seed_profile(db: AsyncSession) -> Profile:
    """Insert a user and a profile with representative content."""
    user = User(
        id=str(uuid4()),
        email=f"cache-test-{uuid4()}@example.com",
        hashed_password="not-a-real-hash",
    )
    profile = Profile(
        id=str(uuid4()),
        user_id=user.id,
        github_username="janedoe",
        portfolio_url="https://janedoe.dev",
        resume_filename="resume.pdf",
        resume_text="Jane Doe. Software Engineer. Python, FastAPI, PostgreSQL.",
    )
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


def completed_review(profile: Profile, created_at: datetime | None = None) -> Review:
    """Build a complete review carrying the profile's current content hash."""
    review = Review(
        id=str(uuid4()),
        profile_id=profile.id,
        status="complete",
        sections=[
            {
                "section_name": "Technical Skills",
                "content": "Feedback on technical skills",
                "confidence": 0.85,
                "suggestions": [],
            }
        ],
        overall_score=0.81,
        content_hash=compute_content_hash(profile),
    )
    if created_at is not None:
        review.created_at = created_at
        review.updated_at = created_at
    return review


@pytest.mark.integration
class TestReviewCachePredicate:
    """The lookup's WHERE clause, exercised through real SQL."""

    @pytest.mark.asyncio
    async def test_unchanged_resubmit_returns_stored_review(self, db: AsyncSession) -> None:
        profile = await seed_profile(db)
        cached = completed_review(profile)
        db.add(cached)
        await db.commit()

        result = await create_review(db, profile.id, profile.user_id)

        assert result.id == cached.id
        assert result.status == "complete"

    @pytest.mark.asyncio
    async def test_changed_content_misses_cache(self, db: AsyncSession) -> None:
        profile = await seed_profile(db)
        cached = completed_review(profile)
        db.add(cached)
        profile.resume_text = "Jane Doe. Senior Engineer. Go, Kubernetes."
        await db.commit()

        result = await create_review(db, profile.id, profile.user_id)

        assert result.id != cached.id
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_failed_review_is_not_a_cache_hit(self, db: AsyncSession) -> None:
        profile = await seed_profile(db)
        failed = completed_review(profile)
        failed.status = "failed"
        db.add(failed)
        await db.commit()

        result = await create_review(db, profile.id, profile.user_id)

        assert result.id != failed.id
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_same_content_on_other_profile_does_not_leak(self, db: AsyncSession) -> None:
        profile_a = await seed_profile(db)
        profile_b = await seed_profile(db)
        cached_a = completed_review(profile_a)
        db.add(cached_a)
        await db.commit()

        result = await create_review(db, profile_b.id, profile_b.user_id)

        assert result.id != cached_a.id
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_hit_returns_newest_matching_review(self, db: AsyncSession) -> None:
        profile = await seed_profile(db)
        older = completed_review(profile, created_at=datetime.utcnow() - timedelta(days=1))
        newer = completed_review(profile)
        db.add(older)
        db.add(newer)
        await db.commit()

        result = await create_review(db, profile.id, profile.user_id)

        assert result.id == newer.id
