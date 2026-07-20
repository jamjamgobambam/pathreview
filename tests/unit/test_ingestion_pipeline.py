"""Unit tests for IngestionPipeline deduplication (issue #13).

These tests document the current broken behavior: the pipeline re-embeds
content it has already ingested, because the skip check and the record
step are both placeholders that never touch the database.

Run with: make test-unit
"""

from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.pipeline import IngestionPipeline

# `make test-unit` runs `pytest tests/unit -v -m unit`; without this marker the
# module is deselected and never runs.
pytestmark = pytest.mark.unit

README_CONTENT = """# Sample Project

A small project used to exercise the ingestion pipeline.

## Installation

Run the installer and follow the prompts.

## Usage

Import the package and call the entry point.
"""

PROFILE_ID = str(uuid4())
REPO_NAME = "sample-project"


def _embedding_calls(pipeline: IngestionPipeline) -> int:
    """Number of times the pipeline handed work to the embedding provider.

    `batch_processor` is a MagicMock in these tests, so the cast tells the type
    checker to expect the mock rather than the real typed method.
    """
    return int(cast(MagicMock, pipeline.batch_processor).process.call_count)


@pytest.fixture
def pipeline() -> IngestionPipeline:
    """Pipeline wired with the session type the application actually produces.

    `core.database.get_db` yields an AsyncSession, so the session is specced
    against AsyncSession rather than a bare MagicMock. A bare MagicMock would
    return a truthy object from any attribute chain, including the placeholder
    `db_session.query(...).filter_by(...).first()`, and the skip test would
    pass for the wrong reason.

    `batch_processor` is replaced after construction so the embedding provider
    is never called and the test runs offline. Its call count is the observable
    that proves whether embedding work was skipped.
    """
    pipeline = IngestionPipeline(
        vector_db=MagicMock(),
        db_session=MagicMock(spec=AsyncSession),
        embedding_provider=MagicMock(),
    )
    pipeline.batch_processor = MagicMock()  # type: ignore[assignment]
    return pipeline


def test_reingesting_unchanged_readme_skips_embedding(pipeline: IngestionPipeline) -> None:
    """Identical content submitted twice should embed once.

    Expected: the second call returns skipped=True and adds no embedding work.
    Actual on main: both calls embed, so process() is called twice.
    """
    first = pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)
    second = pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)

    assert first.skipped is False
    assert second.skipped is True
    assert _embedding_calls(pipeline) == 1


def test_changed_readme_is_ingested_normally(pipeline: IngestionPipeline) -> None:
    """Content that differs by one line must not be skipped."""
    pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)
    second = pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT + "\n## License\n\nMIT\n")

    assert second.skipped is False
    assert _embedding_calls(pipeline) == 2


def test_same_content_under_a_different_profile_is_not_skipped(
    pipeline: IngestionPipeline,
) -> None:
    """Deduplication must be scoped per profile.

    A skip check keyed on the content hash alone would suppress ingestion for
    every profile after the first.
    """
    pipeline.ingest_readme(PROFILE_ID, REPO_NAME, README_CONTENT)
    other = pipeline.ingest_readme(str(uuid4()), REPO_NAME, README_CONTENT)

    assert other.skipped is False
    assert _embedding_calls(pipeline) == 2


def test_check_skip_cannot_query_an_async_session(pipeline: IngestionPipeline) -> None:
    """Root cause, isolated.

    `_check_skip` calls `db_session.query(...)`, which does not exist on
    AsyncSession. The resulting AttributeError is swallowed by a bare
    `except Exception`, so the method returns None and the caller proceeds
    with ingestion as though nothing had been checked.
    """
    result = pipeline._check_skip("readme_abc123", "readme")

    assert result is None

    assert not hasattr(pipeline.db_session, "query")


def test_record_ingested_source_writes_nothing(pipeline: IngestionPipeline) -> None:
    """Second half of the root cause.

    `_record_ingested_source` only logs. Nothing is added to the session, so
    no `ingested_sources` row ever exists for a later skip check to find.
    """
    pipeline._record_ingested_source("readme_abc123", "readme", PROFILE_ID, 4)

    pipeline.db_session.add.assert_not_called()
