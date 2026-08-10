"""Unit tests for rag.retriever.vector_store.VectorStore.

Currently covers delete_collection() (added for issue #80), tested against
a real ChromaDB PersistentClient.
"""

from pathlib import Path

import pytest

from rag.retriever.vector_store import VectorStore


class FakeChunk:
    def __init__(self, id: str, source_id: str, text: str) -> None:
        self.id = id
        self.source_id = source_id
        self.text = text
        self.chunk_index = 0
        self.section = None


@pytest.mark.unit
class TestVectorStoreDeleteCollection:

    @pytest.fixture
    def vector_store(self, tmp_path: Path) -> VectorStore:
        return VectorStore(persist_dir=str(tmp_path / "chromadb"))

    def test_deletes_existing_collection(self, vector_store: VectorStore) -> None:
        """Calling delete_collection() on a collection that has data
        removes it entirely, not just its contents."""
        collection_name = "profile_existing"
        chunk = FakeChunk(id="chunk-1", source_id="source-1", text="hello world")
        vector_store.add_chunks([(chunk, [0.1, 0.2, 0.3])], collection_name)
        assert vector_store.get_collection(collection_name).count() == 1

        vector_store.delete_collection(collection_name)

        remaining = [c.name for c in vector_store.client.list_collections()]
        assert collection_name not in remaining

    def test_deleting_nonexistent_collection_does_not_raise(
        self, vector_store: VectorStore
    ) -> None:
        """Deleting a collection that was never created (e.g. a profile
        with no ingested sources) must not raise — the underlying
        NotFoundError from ChromaDB should be swallowed."""
        vector_store.delete_collection("profile_never_created")

    def test_deleting_twice_does_not_raise(self, vector_store: VectorStore) -> None:
        """A second delete_collection() call on an already-deleted
        collection is also a no-op, not an error (e.g. a retried
        DELETE /profiles/{id} request)."""
        collection_name = "profile_double_delete"
        chunk = FakeChunk(id="chunk-1", source_id="source-1", text="hello world")
        vector_store.add_chunks([(chunk, [0.1, 0.2, 0.3])], collection_name)

        vector_store.delete_collection(collection_name)
        vector_store.delete_collection(collection_name)
