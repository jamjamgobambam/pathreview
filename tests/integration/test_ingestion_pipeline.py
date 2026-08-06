"""
Integration test for the resume ingestion pipeline.

Reproduction (Week 8): confirmed no existing test exercises the full
upload -> parse -> chunk -> embed -> store chain. Manually verified via
python shell that IngestionPipeline.ingest_resume() works end-to-end
when called directly: parses resume text, produces 1 chunk, generates a
mock embedding, and stores it in a real ChromaDB collection.

Also confirmed during reproduction:
- IngestionPipeline is never called from api/routes/profiles.py; the
  upload endpoint parses resumes independently via raw PyPDF2 and never
  invokes the pipeline. This test calls IngestionPipeline directly since
  that's the only place the full chain actually exists today.
- IngestionPipeline._check_skip() has a placeholder query that fails
  against a real SQLAlchemy session; it's wrapped in try/except so
  failures are logged and swallowed rather than raised. As a result,
  re-ingesting identical content currently does NOT skip/dedupe.
- IngestionPipeline._record_ingested_source() only logs; it does not
  persist anything to Postgres despite its docstring.
"""

import uuid

import chromadb
import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline


class FakeDBSession:
    """
    Minimal stand-in for a real SQLAlchemy session.

    IngestionPipeline._check_skip() currently issues a placeholder query
    (db_session.query("IngestedSource")) that isn't valid SQLAlchemy usage.
    That call is wrapped in try/except inside the pipeline, so any session
    that raises on .query() exercises the same (currently-swallowed) code
    path a real session would hit today. This fake makes that behavior
    explicit and documented rather than accidental.
    """

    def query(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "IngestedSource query is a placeholder in IngestionPipeline; "
            "no real ORM query exists yet."
        )


@pytest.fixture
def vector_db() -> chromadb.Collection:
    """Real in-memory ChromaDB collection for this test module."""
    client = chromadb.Client()
    collection_name = f"test_ingestion_pipeline_{uuid.uuid4().hex[:8]}"
    return client.create_collection(collection_name)


@pytest.fixture
def pipeline(vector_db: chromadb.Collection) -> IngestionPipeline:
    return IngestionPipeline(
        vector_db=vector_db,
        db_session=FakeDBSession(),
        embedding_provider=MockEmbeddingProvider(),
    )


@pytest.fixture
def sample_resume_markdown() -> str:
    with open("tests/fixtures/sample_resumes/sample_resume.md") as f:
        return f.read()


@pytest.mark.integration
class TestIngestionPipelineResume:
    """End-to-end tests for the resume ingestion chain: parse -> chunk -> embed -> store."""

    def test_ingest_resume_end_to_end(
        self,
        pipeline: IngestionPipeline,
        vector_db: chromadb.Collection,
        sample_resume_markdown: str,
    ) -> None:
        """A resume fixture should be parsed, chunked, embedded, and stored."""
        result = pipeline.ingest_resume(
            profile_id="test-profile-1",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        assert result.skipped is False
        assert result.chunk_count >= 1
        assert result.source_id.startswith("resume_test-profile-1_")

        # Confirm real storage occurred, not just a returned count
        assert vector_db.count() == result.chunk_count

    def test_ingest_resume_no_experience_section(
        self, pipeline: IngestionPipeline, vector_db: chromadb.Collection
    ) -> None:
        """
        A resume without an Experience section should still ingest without error.

        Note: content is written without leading indentation. ResumeParser's
        section detection (a pre-existing, already-failing unit test:
        test_parse_resume_no_work_experience) does not detect section headers
        when lines are indented, which produces an empty detected_sections
        list. ChromaDB's metadata validation rejects empty list metadata
        values outright, so indented content here would crash storage --
        a real cross-component bug this e2e test surfaced that unit tests
        alone did not catch.
        """
        content = (
            "John Smith\n"
            "Software Developer\n"
            "john@example.com\n\n"
            "Education:\n"
            "- B.S. Computer Science, University (2023)\n\n"
            "Skills: Python, JavaScript, React\n"
        )
        result = pipeline.ingest_resume(
            profile_id="test-profile-2",
            content=content,
            filename="no_experience.md",
        )

        assert result.skipped is False
        assert result.chunk_count >= 1
        assert vector_db.count() == result.chunk_count

    def test_ingest_resume_duplicate_content_does_not_dedupe_today(
        self,
        pipeline: IngestionPipeline,
        vector_db: chromadb.Collection,
        sample_resume_markdown: str,
    ) -> None:
        """
        Documents current (likely unintended) behavior: because
        _check_skip()'s query is a placeholder that fails against any
        real session, ingesting identical content twice does NOT skip
        or dedupe -- it re-ingests and stores again. This test pins down
        that behavior so a future fix to _check_skip() will make this
        test fail loudly, signaling the dedupe path needs to be updated.
        """
        first = pipeline.ingest_resume(
            profile_id="test-profile-3",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )
        second = pipeline.ingest_resume(
            profile_id="test-profile-3",
            content=sample_resume_markdown,
            filename="sample_resume.md",
        )

        assert first.skipped is False
        assert second.skipped is False  # documents current gap: _check_skip never actually skips
        # Note: identical content -> identical content hash -> identical embedding_id,
        # and ChromaDB's add() overwrites on duplicate ID rather than erroring or
        # duplicating. So the collection ends up with 1 entry, not 2, even though
        # the pipeline ran ingestion twice. This is accidental dedup at the vector
        # store layer, not the app's own (broken) _check_skip logic.
        assert vector_db.count() == first.chunk_count
