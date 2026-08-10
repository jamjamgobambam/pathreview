"""Regression test for issue #80: deleting a profile must remove its vector embeddings.

https://github.com/ascherj/pathreview/issues/80

Originally this test reproduced the bug: `DELETE /profiles/{profile_id}` ->
`core.services.profile_service.delete_profile` removed the profile's `reviews`
and `ingested_sources` rows from Postgres but never touched the vector store,
so each profile's embeddings (stored in a dedicated ChromaDB collection named
``profile_{profile_id}`` — see ``rag/retriever/hybrid.py``) were orphaned
forever.

The fix adds ``VectorStore.delete_collection`` and calls it from
``delete_profile``. This test now exercises that real (non-mocked) ChromaDB
behavior end to end: ingest embeddings for two profiles, delete one, and
confirm its collection is gone while the other profile's is untouched.
"""

from dataclasses import dataclass

import pytest

from rag.retriever.vector_store import VectorStore


@dataclass
class _Chunk:
    """Minimal stand-in for an ingested chunk, matching what add_chunks reads."""

    id: str
    source_id: str
    text: str
    chunk_index: int
    section: str | None = None


def _ingest(store: VectorStore, profile_id: str, collection_name: str) -> None:
    source_id = f"resume_{profile_id}_deadbeef"
    chunks = [
        _Chunk(
            id=f"{source_id}_chunk_0",
            source_id=source_id,
            text="Python and FastAPI experience.",
            chunk_index=0,
            section="skills",
        ),
        _Chunk(
            id=f"{source_id}_chunk_1",
            source_id=source_id,
            text="Built REST APIs at TechCorp.",
            chunk_index=1,
            section="experience",
        ),
    ]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    store.add_chunks(list(zip(chunks, embeddings, strict=True)), collection_name)


@pytest.mark.integration
def test_deleting_profile_collection_removes_its_embeddings(tmp_path) -> None:
    store = VectorStore(persist_dir=str(tmp_path / "chromadb"))

    profile_id = "11111111-1111-1111-1111-111111111111"
    collection_name = f"profile_{profile_id}"

    _ingest(store, profile_id, collection_name)
    assert store.get_collection(collection_name).count() == 2, "setup: embeddings should exist"

    # --- Act: this is what delete_profile now does for its vector cleanup. ---
    store.delete_collection(collection_name)

    # A deleted collection is recreated empty by get_collection's
    # get-or-create fallback, so check via list_collections instead of count().
    assert collection_name not in [c.name for c in store.client.list_collections()], (
        f"issue #80: embeddings for deleted profile {profile_id} "
        f"still exist in collection '{collection_name}'"
    )


@pytest.mark.integration
def test_deleting_one_profile_collection_does_not_affect_another(tmp_path) -> None:
    store = VectorStore(persist_dir=str(tmp_path / "chromadb"))

    profile_a = "11111111-1111-1111-1111-111111111111"
    profile_b = "22222222-2222-2222-2222-222222222222"
    collection_a = f"profile_{profile_a}"
    collection_b = f"profile_{profile_b}"

    _ingest(store, profile_a, collection_a)
    _ingest(store, profile_b, collection_b)

    store.delete_collection(collection_a)

    remaining = [c.name for c in store.client.list_collections()]
    assert collection_a not in remaining
    assert collection_b in remaining
    assert store.get_collection(collection_b).count() == 2


@pytest.mark.integration
def test_deleting_collection_for_profile_with_no_embeddings_is_a_noop(tmp_path) -> None:
    """Edge case from PLAN.md: a profile that was never ingested has no
    collection at all — deleting it must not raise."""
    store = VectorStore(persist_dir=str(tmp_path / "chromadb"))

    never_ingested_profile_id = "33333333-3333-3333-3333-333333333333"
    collection_name = f"profile_{never_ingested_profile_id}"

    store.delete_collection(collection_name)  # should not raise
