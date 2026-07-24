"""Reproduction for issue #27 — stale embeddings survive a re-ingest.

https://github.com/ascherj/pathreview/issues/27

When a README is edited and re-ingested, the pipeline stores the new chunks but
never deletes the old ones, so the vector store ends up holding BOTH versions
and the retriever can return stale content.

These tests drive the real ingestion units (IngestionPipeline ->
BatchEmbeddingProcessor) against an in-memory ChromaDB collection.
`test_reingest_leaves_stale_chunks` is EXPECTED TO FAIL on current code — that
failure is the reproduction. Once the fix lands, it becomes the regression test.
"""

import uuid
from unittest.mock import MagicMock

import chromadb
import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline

# Two versions of the same logical README (same profile + repo).
# v1 carries a unique marker absent from v2 -> our staleness probe.
# Both need headings + body, or StructuralChunker emits zero chunks.
README_V1 = """# My Project

## Deprecated Feature
This section documents the OLD_MARKER_XYZ behavior that we are about to remove.
"""

README_V2 = """# My Project

## New Feature
This section documents the brand new behavior. The deprecated part is gone.
"""


@pytest.mark.unit
class TestStaleEmbeddingsReingest:
    """Reproduction suite for stale embeddings after re-ingestion (issue #27)."""

    @pytest.fixture
    def collection(self):
        """Create a real in-memory ChromaDB collection.

        EphemeralClient shares in-process state, so use a unique name per test
        to keep them isolated.
        """
        client = chromadb.EphemeralClient()
        return client.create_collection(name=f"repro_{uuid.uuid4().hex}")

    @pytest.fixture
    def db_session(self):
        """Mock DB session whose skip-check finds no existing source.

        _check_skip() calls db_session.query(...).filter_by(...).first(). A bare
        MagicMock returns a truthy value there, which would make the pipeline
        skip ingestion entirely, so force .first() to return None.
        """
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        return session

    @pytest.fixture
    def pipeline(self, collection, db_session):
        """Create an IngestionPipeline wired to the in-memory collection."""
        return IngestionPipeline(collection, db_session, MockEmbeddingProvider())

    def test_source_id_rotates_on_edit(self, pipeline):
        """Editing the README changes the content-hashed source_id.

        This is why a naive delete-by-current-source_id would match nothing:
        the old chunks live under the previous hash.
        """
        r1 = pipeline.ingest_readme("profile1", "repo1", README_V1)
        r2 = pipeline.ingest_readme("profile1", "repo1", README_V2)

        assert r1.source_id != r2.source_id

    def test_both_versions_are_ingested(self, pipeline):
        """Both re-ingests actually run and produce chunks (neither is skipped)."""
        r1 = pipeline.ingest_readme("profile1", "repo1", README_V1)
        r2 = pipeline.ingest_readme("profile1", "repo1", README_V2)

        assert r1.skipped is False and r2.skipped is False
        assert r1.chunk_count > 0 and r2.chunk_count > 0

    def test_reingest_leaves_stale_chunks(self, pipeline, collection):
        """After re-ingesting v2, the store still holds v1 content (the bug)."""
        pipeline.ingest_readme("profile1", "repo1", README_V1)
        pipeline.ingest_readme("profile1", "repo1", README_V2)

        stored = collection.get()
        all_text = " ".join(stored["documents"])

        assert "OLD_MARKER_XYZ" not in all_text, (
            "stale v1 content is still retrievable after re-ingesting v2 "
            f"({len(stored['ids'])} total chunks in store)"
        )
