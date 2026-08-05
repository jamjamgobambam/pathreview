"""Integration tests for ingestion idempotency (issue #6).

Exercises IngestionPipeline against the real dockerized Postgres and a real
(temporary, on-disk) ChromaDB collection. The unit tests fake the session; these
prove the dedup key survives an actual round trip through the database, the
unique constraint from migration 003, and a genuine vector store.

Requires the compose stack: `make run` / `docker compose up -d db`.
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.config import settings
from core.models.ingested_source import IngestedSource
from core.models.profile import Profile
from core.models.user import User
from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline
from rag.retriever.vector_store import VectorStore

README = """# TaskTracker

A todo app built with FastAPI and React.

## Features

- Create, edit, and complete tasks
- Tag-based filtering and search

## Setup

Run `make dev` and open localhost:3000.
"""


def repo_payload(stars: int, pushed_at: str) -> dict:
    """The same repository as returned by two GitHub fetches at different times."""
    return {
        "name": "tasktracker",
        "description": "A todo app built with FastAPI and React",
        "language": "Python",
        "languages": {"Python": 6000, "TypeScript": 4000},
        "topics": ["fastapi", "react"],
        "html_url": "https://github.com/example/tasktracker",
        "stargazers_count": stars,
        "pushed_at": pushed_at,
    }


class CountingProvider(MockEmbeddingProvider):
    """Deterministic offline provider that counts how often it is billed."""

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return super().embed(texts)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A session on an engine scoped to this test's event loop.

    core.database's module-level engine pools connections against whichever loop
    created them; pytest-asyncio gives each test a fresh loop, so reusing it
    raises "Event loop is closed" on the second test. NullPool + per-test engine
    keeps every connection inside the loop that opened it.
    """
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def profile_id(db_session: AsyncSession) -> AsyncGenerator[str, None]:
    """Create a throwaway user + profile, and clean up everything after."""
    # Hold the IDs as plain strings: a test that rolls back expires its ORM
    # objects, and re-reading user.id during teardown would attempt IO outside
    # SQLAlchemy's greenlet context.
    user_id = str(uuid4())
    new_profile_id = str(uuid4())
    db_session.add(
        User(
            id=user_id,
            email=f"idempotency-{uuid4()}@example.test",
            hashed_password="not-a-real-hash",
        )
    )
    db_session.add(Profile(id=new_profile_id, user_id=user_id, github_username="tasktracker"))
    await db_session.commit()

    yield new_profile_id

    # ingested_sources and profiles cascade from users.
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


@pytest.fixture
def collection(tmp_path: Path) -> Any:
    store = VectorStore(persist_dir=str(tmp_path / "chroma"))
    return store.get_collection("portfolio")


@pytest.fixture
def pipeline(
    collection: Any, db_session: AsyncSession, provider: CountingProvider
) -> IngestionPipeline:
    return IngestionPipeline(
        vector_db=collection, db_session=db_session, embedding_provider=provider
    )


@pytest.fixture
def provider() -> CountingProvider:
    return CountingProvider()


async def count_rows(session: AsyncSession, profile_id: str) -> int:
    result = (
        await session.execute(
            select(func.count())
            .select_from(IngestedSource)
            .where(IngestedSource.profile_id == profile_id)
        )
    ).scalar_one()
    return int(result)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reingesting_identical_readme_is_a_recorded_noop(
    pipeline: IngestionPipeline,
    db_session: AsyncSession,
    profile_id: str,
    collection: Any,
    provider: CountingProvider,
) -> None:
    first = await pipeline.ingest_readme(profile_id, "tasktracker", README)
    vectors_after_first = collection.count()
    calls_after_first = provider.calls

    second = await pipeline.ingest_readme(profile_id, "tasktracker", README)

    assert first.skipped is False
    assert second.skipped is True
    assert second.skip_reason == "Source already ingested"
    assert collection.count() == vectors_after_first
    assert provider.calls == calls_after_first
    assert await count_rows(db_session, profile_id) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reingesting_repo_after_star_change_is_skipped(
    pipeline: IngestionPipeline, db_session: AsyncSession, profile_id: str, collection: Any
) -> None:
    first = await pipeline.ingest_repo_metadata(
        profile_id, repo_payload(41, "2026-07-14T10:00:00Z")
    )
    vectors_after_first = collection.count()

    second = await pipeline.ingest_repo_metadata(
        profile_id, repo_payload(42, "2026-07-21T09:00:00Z")
    )

    assert second.source_id == first.source_id
    assert second.skipped is True
    assert collection.count() == vectors_after_first
    assert await count_rows(db_session, profile_id) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_recorded_row_carries_the_dedup_key_and_full_hash(
    pipeline: IngestionPipeline, db_session: AsyncSession, profile_id: str
) -> None:
    result = await pipeline.ingest_readme(profile_id, "tasktracker", README)

    row = (
        await db_session.execute(
            select(IngestedSource).where(IngestedSource.source_id == result.source_id)
        )
    ).scalar_one()

    assert row.profile_id == profile_id
    assert row.source_type == "readme"
    assert row.chunk_count == result.chunk_count
    assert len(row.content_hash) == 64


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unique_constraint_rejects_a_duplicate_source_id(
    pipeline: IngestionPipeline, db_session: AsyncSession, profile_id: str
) -> None:
    """Migration 003's constraint is what makes the concurrent-ingest race safe."""
    from sqlalchemy.exc import IntegrityError

    result = await pipeline.ingest_readme(profile_id, "tasktracker", README)

    db_session.add(
        IngestedSource(
            profile_id=profile_id,
            source_type="readme",
            source_id=result.source_id,
            content_hash="x" * 64,
            chunk_count=1,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    assert await count_rows(db_session, profile_id) == 1
