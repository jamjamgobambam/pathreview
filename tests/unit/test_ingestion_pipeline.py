"""Tests for ingestion.pipeline.py"""

import pytest

from ingestion.chunking.base import Chunk
from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline


class FakeStrategySelector:
    """Return one deterministic chunk for pipeline unit tests."""

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_index"] = 0
        return [Chunk(text=text, metadata=chunk_metadata)]


class FakeQuery:
    """Minimal query object that supports filter_by().first()."""

    def __init__(self, records: list[object]) -> None:
        self.records = records
        self.filters: dict = {}

    def filter_by(self, **kwargs: object) -> "FakeQuery":
        self.filters.update(kwargs)
        return self

    def first(self) -> object | None:
        for record in self.records:
            if all(getattr(record, key, None) == value for key, value in self.filters.items()):
                return record
        return None


class FakeDBSession:
    """In-memory stand-in for the ingestion pipeline database session."""

    def __init__(self) -> None:
        self.records: list[object] = []

    def query(self, _model: object) -> FakeQuery:
        return FakeQuery(self.records)

    def add(self, record: object) -> None:
        self.records.append(record)

    def commit(self) -> None:
        return None


class RecordingVectorDB:
    """Record vector DB writes without calling ChromaDB."""

    def __init__(self) -> None:
        self.ids: list[str] = []

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        documents: list[str],
    ) -> None:
        self.ids.extend(ids)


@pytest.mark.unit
def test_ingest_repo_metadata_skips_duplicate_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """ingest_repo_metadata() should not write duplicate embeddings for the same repo."""
    monkeypatch.setattr("ingestion.pipeline.StrategySelector", FakeStrategySelector)

    vector_db = RecordingVectorDB()
    db_session = FakeDBSession()
    pipeline = IngestionPipeline(vector_db, db_session, MockEmbeddingProvider())
    repo_data = {
        "name": "portfolio-api",
        "description": "FastAPI portfolio review service",
        "language": "Python",
        "html_url": "https://github.com/example/portfolio-api",
        "readme_content": "# Portfolio API",
        "file_structure": ["app/main.py", "tests/test_main.py", "requirements.txt"],
    }

    first_result = pipeline.ingest_repo_metadata("profile-123", repo_data)
    second_result = pipeline.ingest_repo_metadata("profile-123", repo_data)

    assert first_result.skipped is False
    assert second_result.skipped is True
    assert len(vector_db.ids) == 1
    assert vector_db.ids == [first_result.source_id + "_chunk_0"]
