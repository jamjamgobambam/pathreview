"""Regression test for issue #6: re-ingesting the same source must be skipped."""

from typing import Any

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline, IngestResult

README = """# My Project

## Overview
This is a sample project that does useful things with data pipelines.
"""

OTHER_README = """# My Project

## Overview
A completely different description about machine learning workflows.
"""

RESUME = """# Jane Doe

## Experience
Software Engineer at TechCorp, building REST APIs with Python and FastAPI.

## Skills
Python, JavaScript, PostgreSQL, Docker.
"""

REPO_DATA = {
    "name": "my-repo",
    "description": "A sample project for testing ingestion.",
    "language": "Python",
    "stargazers_count": 12,
    "html_url": "https://github.com/prof-1/my-repo",
}


class FakeVectorDB:
    """Records the ids passed to every add() call, like a ChromaDB collection."""

    def __init__(self) -> None:
        self.added_ids: list[str] = []
        self.add_calls = 0

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        documents: list[str],
    ) -> None:
        self.add_calls += 1
        self.added_ids.extend(ids)


class FakeResult:
    """Minimal stand-in for a SQLAlchemy Result."""

    def __init__(self, records: list[object]) -> None:
        self._records = records

    def scalars(self) -> "FakeResult":
        return self

    def first(self) -> object | None:
        return self._records[0] if self._records else None


class FakeAsyncSession:
    """Stateful stand-in that honours the WHERE clause like a real database."""

    def __init__(self) -> None:
        self.records: list = []

    async def execute(self, stmt: Any) -> FakeResult:
        # Pull the (column == value) pairs out of the WHERE clause so this fake
        # filters the way a real database would
        clause = stmt.whereclause
        comparisons = getattr(clause, "clauses", [clause]) if clause is not None else []
        criteria = {cmp.left.key: cmp.right.value for cmp in comparisons}

        matched = [
            record
            for record in self.records
            if all(getattr(record, column) == value for column, value in criteria.items())
        ]
        return FakeResult(matched)

    def add(self, obj: object) -> None:
        self.records.append(obj)

    async def commit(self) -> None:
        pass


@pytest.mark.unit
@pytest.mark.asyncio
class TestIngestionPipelineDeduplication:
    """Re-ingesting the same source should be skipped, with no duplicate vectors."""

    @pytest.fixture
    def vector_db(self) -> FakeVectorDB:
        return FakeVectorDB()

    @pytest.fixture
    def pipeline(self, vector_db: FakeVectorDB) -> IngestionPipeline:
        return IngestionPipeline(
            vector_db=vector_db,
            db_session=FakeAsyncSession(),
            embedding_provider=MockEmbeddingProvider(),
        )

    def _assert_deduplicated(
        self, first: IngestResult, second: IngestResult, vector_db: FakeVectorDB
    ) -> None:
        assert first.skipped is False
        assert second.skipped is True
        assert first.source_id == second.source_id
        assert vector_db.add_calls == first.chunk_count
        assert len(vector_db.added_ids) == len(set(vector_db.added_ids))

    async def test_reingesting_same_readme_is_skipped(
        self, pipeline: IngestionPipeline, vector_db: FakeVectorDB
    ) -> None:
        first = await pipeline.ingest_readme(
            profile_id="prof-1", repo_name="my-repo", content=README
        )
        second = await pipeline.ingest_readme(
            profile_id="prof-1", repo_name="my-repo", content=README
        )
        self._assert_deduplicated(first, second, vector_db)

    async def test_reingesting_same_resume_is_skipped(
        self, pipeline: IngestionPipeline, vector_db: FakeVectorDB
    ) -> None:
        first = await pipeline.ingest_resume(
            profile_id="prof-1", content=RESUME, filename="resume.md"
        )
        second = await pipeline.ingest_resume(
            profile_id="prof-1", content=RESUME, filename="resume.md"
        )
        self._assert_deduplicated(first, second, vector_db)

    async def test_reingesting_same_repo_is_skipped(
        self, pipeline: IngestionPipeline, vector_db: FakeVectorDB
    ) -> None:
        first = await pipeline.ingest_repo_metadata(profile_id="prof-1", repo_data=REPO_DATA)
        second = await pipeline.ingest_repo_metadata(profile_id="prof-1", repo_data=REPO_DATA)
        self._assert_deduplicated(first, second, vector_db)

    async def test_different_content_is_not_skipped(
        self, pipeline: IngestionPipeline, vector_db: FakeVectorDB
    ) -> None:
        first = await pipeline.ingest_readme(
            profile_id="prof-1", repo_name="my-repo", content=README
        )
        second = await pipeline.ingest_readme(
            profile_id="prof-1", repo_name="my-repo", content=OTHER_README
        )
        # Different content -> different hash -> NOT a duplicate
        assert first.skipped is False
        assert second.skipped is False
        assert first.source_id != second.source_id
        assert vector_db.add_calls == first.chunk_count + second.chunk_count
