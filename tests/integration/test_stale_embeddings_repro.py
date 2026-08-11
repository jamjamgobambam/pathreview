"""Regression test for issue #27 — stale embeddings after README re-ingestion.

https://github.com/ascherj/pathreview/issues/27

Background
----------
When a README was updated and re-ingested, the ingestion pipeline never removed
the previously stored chunks, so the vector store held BOTH the old and the new
embeddings and the retriever could surface content the current README no longer
contained. Two facts combined to cause it:

1. ``IngestionPipeline.ingest_readme`` built the source id with the content hash
   baked in, so an edited README produced a *different* id and its chunks landed
   under brand-new ids instead of overwriting the old ones.
2. ``VectorStore.delete_by_source_id`` existed but was never called, so nothing
   evicted the previous version's chunks.

The fix keys each chunk on a stable, content-independent ``document_id`` and has
the pipeline delete that document's existing chunks before storing the new
version. This test was originally the reproduction (asserting both versions
coexisted); the assertions are now inverted to guard the fix — re-ingesting an
updated README must leave only the current content behind.

This drives the real ``IngestionPipeline`` (parser + structural chunker + batch
processor) against an in-memory ChromaDB collection using the deterministic
``MockEmbeddingProvider``.
"""

import uuid
from unittest.mock import Mock

import chromadb
import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline


def _make_pipeline() -> tuple[IngestionPipeline, "chromadb.api.models.Collection.Collection"]:
    client = chromadb.EphemeralClient()
    collection = client.create_collection(
        name=f"readme_regression_{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"}
    )
    pipeline = IngestionPipeline(
        vector_db=collection,
        db_session=Mock(),
        embedding_provider=MockEmbeddingProvider(),
    )
    return pipeline, collection


@pytest.mark.integration
def test_reingested_readme_leaves_no_stale_chunks() -> None:
    """Re-ingesting an updated README replaces the old chunk instead of adding to it."""
    pipeline, collection = _make_pipeline()
    profile_id, repo_name = "profile1", "weather-app"

    # --- v1: original README, mentions "Flask" ---
    old_content = "# Weather App\nBuilt with Flask and a REST API."
    pipeline.ingest_readme(profile_id, repo_name, old_content)

    # --- v2: README edited; "Flask" replaced with "FastAPI" ---
    new_content = "# Weather App\nBuilt with FastAPI and a REST API."
    pipeline.ingest_readme(profile_id, repo_name, new_content)

    stored_docs = collection.get()["documents"]

    # Fixed behavior (issue #27): only the current README survives.
    assert any("FastAPI" in d for d in stored_docs), "current README content is missing"
    assert not any("Flask" in d for d in stored_docs), "stale v1 chunk was not evicted"

    # A retrieval can therefore never return the outdated "Flask" content.
    query_vec = MockEmbeddingProvider().embed([old_content])[0]
    hits = collection.query(query_embeddings=[query_vec], n_results=5)
    returned_docs = hits["documents"][0]
    assert all("Flask" not in d for d in returned_docs), "retriever returned a stale chunk"


@pytest.mark.integration
def test_unchanged_readme_is_not_reembedded() -> None:
    """Re-ingesting identical content is skipped rather than deleted and rewritten."""
    pipeline, collection = _make_pipeline()
    content = "# Weather App\nBuilt with FastAPI and a REST API."

    first = pipeline.ingest_readme("profile1", "weather-app", content)
    ids_after_first = set(collection.get()["ids"])

    second = pipeline.ingest_readme("profile1", "weather-app", content)

    assert first.skipped is False
    assert second.skipped is True
    assert set(collection.get()["ids"]) == ids_after_first
