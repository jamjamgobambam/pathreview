"""Unit tests for IngestionPipeline deduplication (issue #13).

The pipeline should embed a document once and skip re-embedding when identical
content is submitted again. These tests drive that behavior through a small
in-memory stand-in for the async database session: _record_ingested_source adds
a row, and a later _check_skip finds it and returns a skip result.

Run with: make test-unit
"""

from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from core.models.ingested_source import IngestedSource
from ingestion.pipeline import IngestionPipeline

# `make test-unit` runs `pytest tests/unit -v -m unit`, so every test needs the
# `unit` marker or it is deselected. pytest-asyncio runs in strict mode here (no
# asyncio_mode in pyproject.toml), so each async test also needs `asyncio`. A list
# pytestmark applies both to the whole module, matching the per-test decorators in
# test_review_service.py.
pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

README_CONTENT = """# Sample Project

A small project used to exercise the ingestion pipeline.

## Installation

Run the installer and follow the prompts.

## Usage

Import the package and call the entry point.
"""

PROFILE_ID = str(uuid4())
REPO_NAME = "sample-project"


class _Result:
    """Stands in for the object SQLAlchemy's execute() returns.

    Only the two calls the pipeline makes are modelled: .scalars().first().
    """

    def __init__(self, rows: list[IngestedSource]) -> None:
        self._rows = rows

    def scalars(self) -> "_Result":
        return self

    def first(self) -> IngestedSource | None:
        return self._rows[0] if self._rows else None


class FakeAsyncSession:
    """Minimal in-memory async session for exercising the skip path.

    Rows added via add() are held in a list; execute() matches a
    select() statement's WHERE clause against them on content_hash,
    profile_id, and source_type. This lets a second ingest of the same
    content actually find the row the first ingest recorded, which a
    plain mock cannot do.
    """

    def __init__(self) -> None:
        self.rows: list[IngestedSource] = []
        self.commit_count = 0

    def add(self, row: IngestedSource) -> None:
        self.rows.append(row)

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        pass

    async def execute(self, stmt: object) -> _Result:
        # Pull the three bound comparison values out of the select() WHERE
        # clause and match them against stored rows. Ordering of the clauses
        # follows _check_skip: content_hash, profile_id, source_type.
        criteria = list(stmt.whereclause.clauses)  # type: ignore[attr-defined]
        wanted = {c.left.name: c.right.value for c in criteria}
        matches = [
            r
            for r in self.rows
            if r.content_hash == wanted.get("content_hash")
            and str(r.profile_id) == str(wanted.get("profile_id"))
            and r.source_type == wanted.get("source_type")
        ]
        return _Result(matches)


def _embedding_calls(pipeline: IngestionPipeline) -> int:
    """How many times the pipeline handed work to the embedding provider.

    batch_processor is a MagicMock here, so the cast tells the type checker to
    expect the mock rather than the real typed method. The call count is the
    observable that proves whether embedding was skipped.
    """
    return int(cast("MagicMock", pipeline.batch_processor).process.call_count)


@pytest.fixture
def pipeline() -> IngestionPipeline:
    """Pipeline wired with a stateful fake async session.

    The fake records rows on add() and matches them on execute(), so the
    skip logic is exercised end to end. batch_processor is replaced so no
    embedding provider is called and the tests run offline.
    """
    pipeline = IngestionPipeline(
        vector_db=MagicMock(),
        db_session=FakeAsyncSession(),
        embedding_provider=MagicMock(),
    )
    pipeline.batch_processor = MagicMock()  # type: ignore[assignment]
    return pipeline


async def test_reingesting_unchanged_readme_skips_embedding(
    pipeline: IngestionPipeline,
) -> None:
    """Identical content submitted twice embeds once, then skips."""
    first = await pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)
    second = await pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)

    assert first.skipped is False
    assert second.skipped is True
    assert second.skip_reason == "Source already ingested"
    assert _embedding_calls(pipeline) == 1


async def test_changed_readme_is_ingested_normally(
    pipeline: IngestionPipeline,
) -> None:
    """Content that differs by one line must not be skipped."""
    await pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)
    second = await pipeline.ingest_readme(
        PROFILE_ID, REPO_NAME, README_CONTENT + "\n## License\n\nMIT\n"
    )

    assert second.skipped is False
    assert _embedding_calls(pipeline) == 2


async def test_same_content_under_a_different_profile_is_not_skipped(
    pipeline: IngestionPipeline,
) -> None:
    """Deduplication is scoped per profile.

    A skip keyed on content hash alone would suppress ingestion for every
    profile after the first.
    """
    await pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)
    other = await pipeline.ingest_readme(str(uuid4()), REPO_NAME, README_CONTENT)

    assert other.skipped is False
    assert _embedding_calls(pipeline) == 2


async def test_check_skip_returns_none_when_no_row_exists(
    pipeline: IngestionPipeline,
) -> None:
    """With nothing recorded, the skip check must let ingestion proceed."""
    content_hash = pipeline._hash_content(README_CONTENT)

    result = await pipeline._check_skip(content_hash, PROFILE_ID, "readme")

    assert result is None


async def test_record_ingested_source_persists_a_row(
    pipeline: IngestionPipeline,
) -> None:
    """Recording a source adds exactly one row carrying the content hash and commits."""
    session = cast("FakeAsyncSession", pipeline.db_session)
    content_hash = pipeline._hash_content(README_CONTENT)

    await pipeline._record_ingested_source(PROFILE_ID, "readme", content_hash, 4)

    assert len(session.rows) == 1
    row = session.rows[0]
    assert row.content_hash == content_hash
    assert row.source_type == "readme"
    assert row.chunk_count == 4
    assert session.commit_count == 1


async def test_hash_content_is_full_sha256(pipeline: IngestionPipeline) -> None:
    """The stored hash is the full 64-char digest, not the truncated source_id slice."""
    digest = pipeline._hash_content(README_CONTENT)

    assert len(digest) == 64
    assert digest == pipeline._hash_content(README_CONTENT.encode())


async def test_record_ingested_source_propagates_db_errors(
    pipeline: IngestionPipeline,
) -> None:
    """A database error while recording surfaces instead of being swallowed.

    The session is shared per request, so _record_ingested_source must not roll
    back (that would discard a caller's pending writes) or swallow the error
    (that would return a successful-looking result after failing to persist).
    The exception is expected to propagate.
    """
    session = cast("FakeAsyncSession", pipeline.db_session)

    async def _raise() -> None:
        raise SQLAlchemyError("commit failed")

    session.commit = _raise  # type: ignore[method-assign]
    content_hash = pipeline._hash_content(README_CONTENT)

    with pytest.raises(SQLAlchemyError):
        await pipeline._record_ingested_source(PROFILE_ID, "readme", content_hash, 4)
