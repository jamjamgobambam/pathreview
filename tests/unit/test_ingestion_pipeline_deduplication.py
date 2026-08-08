from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from core.models.ingested_source import IngestedSource
from ingestion.chunking.base import Chunk
from ingestion.parsers.base import ParseResult
from ingestion.pipeline import IngestionPipeline


class _ScalarResult:
    """Minimal SQLAlchemy result substitute for pipeline unit tests."""

    def __init__(self, value: IngestedSource | None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> IngestedSource | None:
        return self._value


class _FakeAsyncSession:
    """In-memory AsyncSession substitute that persists sources by source_id."""

    def __init__(self) -> None:
        self.records: dict[str, IngestedSource] = {}
        self._pending: IngestedSource | None = None

    async def execute(self, statement: Any) -> _ScalarResult:
        parameters = statement.compile().params
        source_id = next(value for key, value in parameters.items() if "source_id" in key)
        return _ScalarResult(self.records.get(str(source_id)))

    def add(self, record: IngestedSource) -> None:
        self._pending = record

    async def commit(self) -> None:
        if self._pending is None:
            return

        if self._pending.source_id is None:
            raise AssertionError("Test record must have a source_id")

        self.records[self._pending.source_id] = self._pending
        self._pending = None

    async def rollback(self) -> None:
        self._pending = None


def _create_pipeline(
    session: _FakeAsyncSession,
) -> IngestionPipeline:
    return IngestionPipeline(
        vector_db=MagicMock(),
        db_session=cast(Any, session),
        embedding_provider=cast(Any, MagicMock()),
    )


def _parse_result() -> ParseResult:
    return ParseResult(
        text="Sample repository metadata",
        metadata={
            "primary_language": "Python",
            "tech_stack": ["Python"],
        },
        source_type="repo",
    )


def _chunks() -> list[Chunk]:
    return [
        Chunk(
            text="Sample repository metadata",
            metadata={"chunk_index": 0},
        )
    ]


@pytest.mark.asyncio
async def test_reingesting_identical_repository_skips_embeddings() -> None:
    """Identical repository data should only be embedded once."""
    session = _FakeAsyncSession()
    pipeline = _create_pipeline(session)

    repo_data = {
        "name": "sample-repository",
        "html_url": "https://github.com/example/sample-repository",
        "description": "Sample project",
        "language": "Python",
    }

    with (
        patch.object(
            pipeline.repo_analyzer,
            "parse",
            return_value=_parse_result(),
        ),
        patch.object(
            pipeline.strategy_selector,
            "chunk",
            return_value=_chunks(),
        ),
        patch.object(
            pipeline.batch_processor,
            "process",
            return_value=[],
        ) as process_mock,
    ):
        first_result = await pipeline.ingest_repo_metadata(
            "00000000-0000-0000-0000-000000000001",
            repo_data,
        )
        second_result = await pipeline.ingest_repo_metadata(
            "00000000-0000-0000-0000-000000000001",
            repo_data,
        )

    assert first_result.skipped is False
    assert second_result.skipped is True
    assert process_mock.call_count == 1
    assert len(session.records) == 1


@pytest.mark.asyncio
async def test_volatile_repo_metrics_do_not_trigger_reingestion() -> None:
    """Changing star counts should not change repository identity."""
    session = _FakeAsyncSession()
    pipeline = _create_pipeline(session)

    initial_data = {
        "name": "sample-repository",
        "html_url": "https://github.com/example/sample-repository",
        "description": "Sample project",
        "language": "Python",
        "stargazers_count": 10,
    }
    refreshed_data = {
        **initial_data,
        "stargazers_count": 11,
    }

    with (
        patch.object(
            pipeline.repo_analyzer,
            "parse",
            return_value=_parse_result(),
        ),
        patch.object(
            pipeline.strategy_selector,
            "chunk",
            return_value=_chunks(),
        ),
        patch.object(
            pipeline.batch_processor,
            "process",
            return_value=[],
        ) as process_mock,
    ):
        await pipeline.ingest_repo_metadata(
            "00000000-0000-0000-0000-000000000001",
            initial_data,
        )
        second_result = await pipeline.ingest_repo_metadata(
            "00000000-0000-0000-0000-000000000001",
            refreshed_data,
        )

    assert second_result.skipped is True
    assert process_mock.call_count == 1


@pytest.mark.asyncio
async def test_meaningful_repo_change_triggers_new_ingestion() -> None:
    """Changing repository content should produce a new ingestion."""
    session = _FakeAsyncSession()
    pipeline = _create_pipeline(session)

    initial_data = {
        "name": "sample-repository",
        "html_url": "https://github.com/example/sample-repository",
        "description": "Initial description",
        "language": "Python",
    }
    changed_data = {
        **initial_data,
        "description": "Updated description",
    }

    with (
        patch.object(
            pipeline.repo_analyzer,
            "parse",
            return_value=_parse_result(),
        ),
        patch.object(
            pipeline.strategy_selector,
            "chunk",
            return_value=_chunks(),
        ),
        patch.object(
            pipeline.batch_processor,
            "process",
            return_value=[],
        ) as process_mock,
    ):
        first_result = await pipeline.ingest_repo_metadata(
            "00000000-0000-0000-0000-000000000001",
            initial_data,
        )
        second_result = await pipeline.ingest_repo_metadata(
            "00000000-0000-0000-0000-000000000001",
            changed_data,
        )

    assert first_result.skipped is False
    assert second_result.skipped is False
    assert process_mock.call_count == 2
    assert len(session.records) == 2
