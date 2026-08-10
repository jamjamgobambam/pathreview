"""End-to-end integration test for the resume ingestion pipeline.

Drives ``IngestionPipeline.ingest_resume()`` from a sample resume fixture all the
way through parsing, chunking, embedding, and storage, asserting on both the
returned ``IngestResult`` and the side effects captured at the storage seam.

The test is hermetic: it uses the real parser/chunker/pipeline code but swaps in
the offline ``MockEmbeddingProvider`` and a lightweight in-memory vector-DB spy,
so it needs no network, API keys, or Docker services.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline, IngestResult

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "sample_resumes"
EMBEDDING_DIM = MockEmbeddingProvider.EMBEDDING_DIM


class FakeVectorDB:
    """In-memory stand-in for a ChromaDB collection.

    Records every ``add()`` call so tests can assert on what was stored. A real
    ChromaDB collection is deliberately avoided: chunk metadata includes list
    values (e.g. ``detected_sections``) that ChromaDB's scalar-only metadata
    constraint would reject.
    """

    def __init__(self):
        self.ids: list[str] = []
        self.embeddings: list[list[float]] = []
        self.metadatas: list[dict] = []
        self.documents: list[str] = []
        self.add_call_count = 0

    def add(self, ids, embeddings, metadatas, documents):
        self.add_call_count += 1
        self.ids.extend(ids)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)
        self.documents.extend(documents)


@pytest.mark.integration
class TestResumeIngestionPipeline:
    """End-to-end coverage for the resume ingestion flow."""

    @pytest.fixture
    def sample_resume_markdown(self) -> str:
        """Load the sample resume fixture from disk (as an upload would supply)."""
        return (FIXTURE_DIR / "sample_resume.md").read_text(encoding="utf-8")

    @pytest.fixture
    def vector_db(self) -> FakeVectorDB:
        """A fresh in-memory vector-DB spy for each test."""
        return FakeVectorDB()

    @pytest.fixture
    def db_session(self) -> Mock:
        """A DB session whose dedup lookup finds nothing, so ingestion proceeds.

        ``IngestionPipeline._check_skip`` calls
        ``db_session.query(...).filter_by(...).first()``; returning ``None`` here
        keeps the pipeline from short-circuiting as an already-ingested source.
        """
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        return session

    @pytest.fixture
    def pipeline(self, vector_db, db_session) -> IngestionPipeline:
        """Pipeline wired with real components and offline test doubles."""
        return IngestionPipeline(
            vector_db=vector_db,
            db_session=db_session,
            embedding_provider=MockEmbeddingProvider(),
        )

    def test_ingest_resume_end_to_end(self, pipeline, vector_db, sample_resume_markdown):
        """A sample resume flows through every stage and lands as stored embeddings."""
        result = pipeline.ingest_resume(
            profile_id="profile-123",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        # --- Returned result ---
        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.skip_reason is None
        assert result.source_id.startswith("resume_profile-123_")
        assert result.chunk_count >= 1

        # --- Storage side effects (the seam this test exists to protect) ---
        assert vector_db.add_call_count >= 1
        # Every chunk the pipeline reported was actually stored, exactly once.
        assert len(vector_db.ids) == result.chunk_count
        assert len(set(vector_db.ids)) == result.chunk_count
        assert len(vector_db.embeddings) == result.chunk_count
        assert len(vector_db.documents) == result.chunk_count

    def test_stored_embeddings_have_expected_shape(
        self, pipeline, vector_db, sample_resume_markdown
    ):
        """Each stored embedding is a full-dimensional numeric vector."""
        pipeline.ingest_resume(
            profile_id="p1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        assert vector_db.embeddings, "expected at least one stored embedding"
        for embedding in vector_db.embeddings:
            assert len(embedding) == EMBEDDING_DIM
            assert all(isinstance(value, float) for value in embedding)

    def test_metadata_propagated_through_pipeline(
        self, pipeline, vector_db, sample_resume_markdown
    ):
        """Top-level inputs and parser output survive all the way to storage."""
        result = pipeline.ingest_resume(
            profile_id="p1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        assert vector_db.metadatas
        for index, metadata in enumerate(vector_db.metadatas):
            # Injected by the pipeline before chunking.
            assert metadata["source_id"] == result.source_id
            assert metadata["profile_id"] == "p1"
            assert metadata["filename"] == "sample_resume.md"
            assert metadata["source_type"] == "resume"
            # Added by the chunker.
            assert metadata["chunk_index"] == index
            # Produced by the parser and carried through untouched.
            assert "detected_sections" in metadata

    def test_stored_documents_match_chunk_text(self, pipeline, vector_db, sample_resume_markdown):
        """The documents stored are the real (non-empty) chunk texts."""
        pipeline.ingest_resume(
            profile_id="p1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        assert vector_db.documents
        assert all(doc.strip() for doc in vector_db.documents)

    def test_embedding_ids_follow_source_chunk_convention(
        self, pipeline, vector_db, sample_resume_markdown
    ):
        """Stored IDs follow the ``{source_id}_chunk_{index}`` convention."""
        result = pipeline.ingest_resume(
            profile_id="p1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        expected = [f"{result.source_id}_chunk_{index}" for index in range(result.chunk_count)]
        assert vector_db.ids == expected

    def test_duplicate_source_is_skipped(
        self, pipeline, vector_db, db_session, sample_resume_markdown
    ):
        """When the source already exists, ingestion skips without storing."""
        # Make the dedup lookup report an existing source.
        db_session.query.return_value.filter_by.return_value.first.return_value = object()

        result = pipeline.ingest_resume(
            profile_id="p1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        assert result.skipped is True
        assert result.skip_reason == "Source already ingested"
        assert result.chunk_count == 0
        assert vector_db.add_call_count == 0
        assert vector_db.ids == []

    def test_empty_resume_does_not_crash(self, pipeline, vector_db):
        """A whitespace-only resume is handled gracefully with nothing stored."""
        result = pipeline.ingest_resume(
            profile_id="p1",
            content="   \n\t  \n",
            filename="empty.md",
        )

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.chunk_count == 0
        assert vector_db.add_call_count == 0

    def test_ingestion_is_deterministic(self, pipeline, vector_db, sample_resume_markdown):
        """Re-embedding identical text yields identical vectors (hash-seeded mock)."""
        pipeline.ingest_resume(
            profile_id="p1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )
        first_pass = list(vector_db.embeddings)

        provider = MockEmbeddingProvider()
        again = provider.embed(list(vector_db.documents))

        assert again == first_pass
