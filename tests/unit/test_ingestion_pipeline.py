"""Unit tests for IngestionPipeline re-ingestion behavior (issue #27).

These exercise the delete-before-insert logic that keeps the vector store from
holding stale chunks after a document is edited and re-ingested. They drive the
real pipeline (parser + structural chunker + batch processor) against an
in-memory ChromaDB collection, using the deterministic MockEmbeddingProvider so
no network or external services are required.
"""

import uuid
from unittest.mock import Mock

import chromadb
import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline


def _make_pipeline() -> tuple[IngestionPipeline, "chromadb.api.models.Collection.Collection"]:
    """Build a pipeline backed by a fresh in-memory ChromaDB collection."""
    client = chromadb.EphemeralClient()
    collection = client.create_collection(
        name=f"pipeline_test_{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"}
    )
    pipeline = IngestionPipeline(
        vector_db=collection,
        db_session=Mock(),
        embedding_provider=MockEmbeddingProvider(),
    )
    return pipeline, collection


@pytest.mark.unit
class TestReadmeReingestion:
    """Re-ingesting an updated README must fully replace the previous version."""

    def test_reingested_readme_evicts_stale_chunks(self):
        """After re-ingestion the store holds only the current README content."""
        pipeline, collection = _make_pipeline()
        profile_id, repo_name = "profile1", "weather-app"

        old = "# Weather App\nBuilt with Flask and a REST API."
        new = "# Weather App\nBuilt with FastAPI and a REST API."

        pipeline.ingest_readme(profile_id, repo_name, old)
        pipeline.ingest_readme(profile_id, repo_name, new)

        docs = collection.get()["documents"]
        assert any("FastAPI" in d for d in docs), "current README content is missing"
        assert not any("Flask" in d for d in docs), "stale README content was not evicted"

    def test_retrieval_never_returns_stale_content(self):
        """A query after re-ingestion cannot surface the pre-update chunk."""
        pipeline, collection = _make_pipeline()
        provider = MockEmbeddingProvider()
        profile_id, repo_name = "profile1", "weather-app"

        pipeline.ingest_readme(profile_id, repo_name, "# App\nBuilt with Flask.")
        pipeline.ingest_readme(profile_id, repo_name, "# App\nBuilt with FastAPI.")

        # Query with the embedding of the *old* content; the stale chunk is gone,
        # so it can never be returned.
        query_vec = provider.embed(["# App\nBuilt with Flask."])[0]
        hits = collection.query(query_embeddings=[query_vec], n_results=5)
        returned = hits["documents"][0]
        assert all("Flask" not in d for d in returned)

    def test_unchanged_readme_is_skipped(self):
        """Re-ingesting identical content is skipped, not deleted-and-reinserted."""
        pipeline, collection = _make_pipeline()
        content = "# Weather App\nBuilt with FastAPI."

        first = pipeline.ingest_readme("profile1", "weather-app", content)
        count_after_first = len(collection.get()["ids"])

        second = pipeline.ingest_readme("profile1", "weather-app", content)

        assert first.skipped is False
        assert second.skipped is True
        assert second.chunk_count == 0
        # Nothing was added or removed on the no-op re-ingestion.
        assert len(collection.get()["ids"]) == count_after_first

    def test_first_ingestion_delete_is_safe_noop(self):
        """First-time ingestion (no prior chunks) stores chunks without error."""
        pipeline, collection = _make_pipeline()

        result = pipeline.ingest_readme("profile1", "weather-app", "# App\nHello.")

        assert result.skipped is False
        assert result.chunk_count >= 1
        assert len(collection.get()["ids"]) >= 1

    def test_shrinking_readme_removes_leftover_chunks(self):
        """A shorter v2 must not leave high-index chunks from a longer v1 behind."""
        pipeline, collection = _make_pipeline()
        profile_id, repo_name = "profile1", "big-repo"

        big = "# Intro\nIntro text.\n" "# Setup\nSetup text.\n" "# Usage\nUsage text.\n"
        small = "# Intro\nJust the intro now."

        pipeline.ingest_readme(profile_id, repo_name, big)
        big_chunks = len(collection.get()["ids"])

        pipeline.ingest_readme(profile_id, repo_name, small)
        docs = collection.get()["documents"]

        assert big_chunks > len(docs), "expected fewer chunks after shrinking"
        assert not any("Setup text" in d for d in docs)
        assert not any("Usage text" in d for d in docs)

    def test_reingestion_is_isolated_per_profile(self):
        """Re-ingesting one profile's README must not touch another profile's chunks."""
        pipeline, collection = _make_pipeline()
        repo_name = "shared-name"

        pipeline.ingest_readme("profileA", repo_name, "# A\nUses Django.")
        pipeline.ingest_readme("profileB", repo_name, "# B\nUses Rails.")

        # Update profile A only.
        pipeline.ingest_readme("profileA", repo_name, "# A\nUses Flask now.")

        docs = collection.get()["documents"]
        assert any("Rails" in d for d in docs), "profile B's chunk was wrongly deleted"
        assert any("Flask" in d for d in docs), "profile A's updated chunk is missing"
        assert not any("Django" in d for d in docs), "profile A's stale chunk survived"
