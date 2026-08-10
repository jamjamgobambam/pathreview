"""Tests for rag/retriever/vector_store.py, focused on VectorStore.delete_collection
added for issue #80 (DELETE /profiles/{profile_id} orphaned embeddings)."""

import pytest

from rag.retriever.vector_store import VectorStore


@pytest.mark.unit
class TestDeleteCollection:
    """Test suite for VectorStore.delete_collection."""

    @pytest.fixture
    def store(self, tmp_path):
        return VectorStore(persist_dir=str(tmp_path / "chromadb"))

    def test_removes_an_existing_collection(self, store):
        collection_name = "profile_test-1"
        store.get_collection(collection_name)
        assert collection_name in [c.name for c in store.client.list_collections()]

        store.delete_collection(collection_name)

        assert collection_name not in [c.name for c in store.client.list_collections()]

    def test_is_a_noop_when_collection_does_not_exist(self, store):
        """A profile that was never ingested has no collection at all —
        deleting it must not raise."""
        store.delete_collection("profile_never-created")  # should not raise

    def test_only_deletes_the_named_collection(self, store):
        store.get_collection("profile_a")
        store.get_collection("profile_b")

        store.delete_collection("profile_a")

        remaining = [c.name for c in store.client.list_collections()]
        assert "profile_a" not in remaining
        assert "profile_b" in remaining
