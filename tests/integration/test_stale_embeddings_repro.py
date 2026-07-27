"""Reproduction for issue #27 — stale embeddings persist after README re-ingestion.

https://github.com/ascherj/pathreview/issues/27

Root cause
----------
When a README is updated and re-ingested, the ingestion pipeline never removes
the previously stored chunks, so the vector store ends up holding BOTH the old
and the new embeddings. Two facts in the codebase combine to cause this:

1. `ingestion/pipeline.py::IngestionPipeline.ingest_readme` builds the source id
   as ``f"readme_{profile_id}_{repo_name}_{self._hash_content(content)}"``. The
   content hash is part of the id, so an edited README produces a *different*
   source_id and its chunks land under brand-new ids instead of overwriting the
   old ones.

2. `rag/retriever/vector_store.py::VectorStore.delete_by_source_id` exists but is
   never called anywhere in the pipeline (verified: it has no callers). Nothing
   ever evicts the previous version's chunks.

Result: the retriever can surface chunks that describe content the current
README no longer contains.

This test reproduces the bug by mimicking exactly what the pipeline does today
(embedding id == ``f"{source_id}_chunk_{chunk_index}"`` per
`ingestion/embeddings/batch_processor.py::_store_embedding`). It asserts the
CURRENT (buggy) behavior so it passes today and proves the bug is real. Once the
fix lands, the assertion marked ``BUG`` below should be inverted to assert that
the stale chunk is gone.
"""

import hashlib

import chromadb
import pytest
from chromadb.api.models.Collection import Collection


def _hash_content(content: str) -> str:
    """Mirror IngestionPipeline._hash_content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _readme_source_id(profile_id: str, repo_name: str, content: str) -> str:
    """Mirror the source_id scheme in IngestionPipeline.ingest_readme."""
    return f"readme_{profile_id}_{repo_name}_{_hash_content(content)}"


def _ingest(
    collection: Collection,
    profile_id: str,
    repo_name: str,
    content: str,
    embedding: list[float],
) -> str:
    """Simulate one README ingestion the way the pipeline does it today.

    Stores a single chunk (chunk_index=0) with an id of
    ``f"{source_id}_chunk_0"`` — matching batch_processor._store_embedding.
    Critically, it performs NO deletion of prior chunks, exactly like the
    real pipeline.
    """
    source_id = _readme_source_id(profile_id, repo_name, content)
    embedding_id = f"{source_id}_chunk_0"
    collection.add(
        ids=[embedding_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"source_id": source_id, "chunk_index": 0, "source_type": "readme"}],
    )
    return source_id


@pytest.mark.integration
def test_stale_embeddings_remain_after_readme_reingestion() -> None:
    """Re-ingesting an updated README leaves the old chunk in the store."""
    client = chromadb.EphemeralClient()
    collection = client.create_collection(name="readme_repro", metadata={"hnsw:space": "cosine"})

    profile_id, repo_name = "profile1", "weather-app"

    # --- v1: original README, mentions "Flask" ---
    old_content = "# Weather App\nBuilt with Flask and a REST API."
    old_source_id = _ingest(collection, profile_id, repo_name, old_content, [0.1, 0.2, 0.3])

    # --- v2: README edited; "Flask" replaced with "FastAPI" ---
    new_content = "# Weather App\nBuilt with FastAPI and a REST API."
    new_source_id = _ingest(collection, profile_id, repo_name, new_content, [0.11, 0.21, 0.31])

    # The content change produced a different source_id, so nothing overwrote v1.
    assert old_source_id != new_source_id

    stored = collection.get()
    stored_docs = stored["documents"]

    # BUG (issue #27): BOTH versions are present. The store should contain only
    # the current README, but the stale "Flask" chunk was never evicted.
    assert old_content in stored_docs, "expected the stale v1 chunk to still be present (bug)"
    assert new_content in stored_docs
    assert (
        len(stored["ids"]) == 2
    ), f"expected 2 chunks (1 stale + 1 current), got {len(stored['ids'])}"

    # A retrieval can therefore return outdated content ("Flask") that no longer
    # reflects the live README ("FastAPI").
    hits = collection.query(query_embeddings=[[0.1, 0.2, 0.3]], n_results=2)
    returned_docs = hits["documents"][0]
    assert old_content in returned_docs, "retriever returned the stale chunk (bug reproduced)"
