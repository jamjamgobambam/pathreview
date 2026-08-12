"""Tests for ingestion pipeline deduplication."""

import hashlib
from typing import cast
from unittest.mock import MagicMock

import pytest

from core.models.ingested_source import IngestedSource
from ingestion.pipeline import IngestionPipeline


class FakeQuery:
    """Small query helper for matching records added to the fake session."""

    def __init__(self, records: list[IngestedSource]) -> None:
        self.records = records
        self.filters: dict[str, object] = {}

    def filter_by(self, **filters: object) -> "FakeQuery":
        """Store equality filters for the later first() call."""
        self.filters = filters
        return self

    def first(self) -> IngestedSource | None:
        """Return the first record matching all filter values."""
        for record in self.records:
            if all(getattr(record, field) == value for field, value in self.filters.items()):
                return record
        return None


class FakeSession:
    """In-memory stand-in for the SQLAlchemy calls used by the pipeline."""

    def __init__(self, fail_lookup: bool = False) -> None:
        self.records: list[IngestedSource] = []
        self.fail_lookup = fail_lookup

    def query(self, model: type[IngestedSource]) -> FakeQuery:
        """Return a query object or simulate a database lookup failure."""
        if self.fail_lookup:
            raise RuntimeError("database lookup failed")
        assert model is IngestedSource
        return FakeQuery(self.records)

    def add(self, record: IngestedSource) -> None:
        """Persist a record in memory."""
        self.records.append(record)


def build_pipeline(
    sample_readme_text: str,
    db_session: FakeSession | None = None,
) -> tuple[IngestionPipeline, FakeSession]:
    """Create an ingestion pipeline with parsing, chunking, and embedding mocked."""
    session = db_session or FakeSession()
    pipeline = IngestionPipeline(
        vector_db=MagicMock(),
        db_session=session,
        embedding_provider=MagicMock(),
    )

    parse_result = MagicMock()
    parse_result.text = sample_readme_text
    parse_result.metadata = {
        "heading_count": 2,
        "word_count": 20,
    }

    pipeline.readme_parser.parse = MagicMock(return_value=parse_result)  # type: ignore[method-assign]
    pipeline.strategy_selector.chunk = MagicMock(  # type: ignore[method-assign]
        return_value=[MagicMock(), MagicMock()]
    )
    pipeline.batch_processor.process = MagicMock()  # type: ignore[method-assign]
    return pipeline, session


def expected_sha256(content: str | bytes) -> str:
    """Return the full SHA-256 hash for test assertions."""
    if isinstance(content, str):
        content = content.encode()
    return hashlib.sha256(content).hexdigest()


def parse_call_count(pipeline: IngestionPipeline) -> int:
    """Return how many times the README parser mock was called."""
    return cast("MagicMock", pipeline.readme_parser.parse).call_count


def chunk_call_count(pipeline: IngestionPipeline) -> int:
    """Return how many times the chunking mock was called."""
    return cast("MagicMock", pipeline.strategy_selector.chunk).call_count


def embedding_call_count(pipeline: IngestionPipeline) -> int:
    """Return how many times the embedding processor mock was called."""
    return cast("MagicMock", pipeline.batch_processor.process).call_count


@pytest.mark.unit
def test_first_readme_ingestion_processes_and_records_source(
    sample_readme_text: str,
) -> None:
    """First README ingestion should parse, embed, and record metadata."""
    pipeline, session = build_pipeline(sample_readme_text)

    result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )

    assert result.skipped is False
    assert result.chunk_count == 2
    assert parse_call_count(pipeline) == 1
    assert chunk_call_count(pipeline) == 1
    assert embedding_call_count(pipeline) == 1

    assert len(session.records) == 1
    record = session.records[0]
    assert record.profile_id == "profile-123"
    assert record.source_type == "readme"
    assert record.source_url == "weather-app"
    assert record.content_hash == expected_sha256(sample_readme_text)
    assert len(record.content_hash or "") == 64
    assert record.chunk_count == 2


@pytest.mark.unit
def test_same_readme_same_profile_and_repo_is_skipped_without_processing_again(
    sample_readme_text: str,
) -> None:
    """Duplicate README content for the same profile and repo should skip work."""
    pipeline, session = build_pipeline(sample_readme_text)

    first_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )
    second_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )

    assert first_result.skipped is False
    assert second_result.skipped is True
    assert second_result.chunk_count == 0
    assert second_result.skip_reason == "Source content has not changed"
    assert parse_call_count(pipeline) == 1
    assert chunk_call_count(pipeline) == 1
    assert embedding_call_count(pipeline) == 1
    assert len(session.records) == 1


@pytest.mark.unit
def test_changed_readme_content_is_processed(sample_readme_text: str) -> None:
    """Changed content should create a new hash and run embedding again."""
    pipeline, session = build_pipeline(sample_readme_text)
    changed_readme = f"{sample_readme_text}\n## Deployment\nHosted on Vercel."

    first_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )
    second_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=changed_readme,
    )

    assert first_result.skipped is False
    assert second_result.skipped is False
    assert embedding_call_count(pipeline) == 2
    assert len(session.records) == 2
    assert session.records[0].content_hash != session.records[1].content_hash


@pytest.mark.unit
def test_same_readme_content_for_different_profile_is_processed(
    sample_readme_text: str,
) -> None:
    """The same README text should not be skipped for a different profile."""
    pipeline, session = build_pipeline(sample_readme_text)

    first_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )
    second_result = pipeline.ingest_readme(
        profile_id="profile-456",
        repo_name="weather-app",
        content=sample_readme_text,
    )

    assert first_result.skipped is False
    assert second_result.skipped is False
    assert embedding_call_count(pipeline) == 2
    assert len(session.records) == 2


@pytest.mark.unit
def test_same_readme_content_for_different_repo_is_processed(
    sample_readme_text: str,
) -> None:
    """The same README text should not be skipped for a different repository."""
    pipeline, session = build_pipeline(sample_readme_text)

    first_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )
    second_result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="forecast-dashboard",
        content=sample_readme_text,
    )

    assert first_result.skipped is False
    assert second_result.skipped is False
    assert embedding_call_count(pipeline) == 2
    assert len(session.records) == 2
    assert session.records[0].source_url != session.records[1].source_url


@pytest.mark.unit
def test_string_and_byte_content_produce_same_full_hash(
    sample_readme_text: str,
) -> None:
    """Equivalent string and byte content should hash to the same full value."""
    pipeline, _session = build_pipeline(sample_readme_text)

    string_hash = pipeline._hash_content(sample_readme_text)
    byte_hash = pipeline._hash_content(sample_readme_text.encode())

    assert string_hash == byte_hash
    assert string_hash == expected_sha256(sample_readme_text)
    assert len(string_hash) == 64


@pytest.mark.unit
def test_database_lookup_failure_does_not_report_duplicate(
    sample_readme_text: str,
) -> None:
    """A lookup error should allow processing instead of falsely skipping."""
    pipeline, session = build_pipeline(
        sample_readme_text,
        db_session=FakeSession(fail_lookup=True),
    )

    result = pipeline.ingest_readme(
        profile_id="profile-123",
        repo_name="weather-app",
        content=sample_readme_text,
    )

    assert result.skipped is False
    assert parse_call_count(pipeline) == 1
    assert chunk_call_count(pipeline) == 1
    assert embedding_call_count(pipeline) == 1
    assert len(session.records) == 1
