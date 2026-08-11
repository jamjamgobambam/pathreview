"""Unit tests for VectorStore deletion primitives (issue #27).

Focus on delete_by_document_id, the content-independent cleanup used to evict a
previous version of a document on re-ingestion, and on confirming
delete_by_source_id only removes the exact content version it targets.
"""

import pytest

from rag.retriever.vector_store import VectorStore


def _seed(store: VectorStore, collection_name: str) -> None:
    """Store two versions of one document plus an unrelated document."""
    collection = store.get_collection(collection_name)
    collection.add(
        ids=["readme_p_repo_v1_chunk_0", "readme_p_repo_v2_chunk_0", "readme_p_other_chunk_0"],
        embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
        documents=["old flask readme", "new fastapi readme", "unrelated readme"],
        metadatas=[
            {"source_id": "readme_p_repo_v1", "document_id": "readme_p_repo"},
            {"source_id": "readme_p_repo_v2", "document_id": "readme_p_repo"},
            {"source_id": "readme_p_other_v1", "document_id": "readme_p_other"},
        ],
    )


@pytest.fixture
def store(tmp_path) -> VectorStore:
    """A VectorStore persisted to a throwaway temp directory."""
    return VectorStore(persist_dir=str(tmp_path / "chroma"))


@pytest.mark.unit
class TestDeleteByDocumentId:
    """delete_by_document_id removes every version of one document only."""

    def test_removes_all_versions_of_document(self, store):
        _seed(store, "col")

        store.delete_by_document_id("readme_p_repo", "col")

        remaining = store.get_collection("col").get()
        assert remaining["ids"] == ["readme_p_other_chunk_0"]

    def test_does_not_touch_other_documents(self, store):
        _seed(store, "col")

        store.delete_by_document_id("readme_p_repo", "col")

        docs = store.get_collection("col").get()["documents"]
        assert "unrelated readme" in docs

    def test_missing_document_is_noop(self, store):
        _seed(store, "col")

        # Should not raise and should delete nothing.
        store.delete_by_document_id("does_not_exist", "col")

        assert len(store.get_collection("col").get()["ids"]) == 3

    def test_empty_collection_is_noop(self, store):
        store.get_collection("empty")  # create but add nothing

        store.delete_by_document_id("anything", "empty")

        assert store.get_collection("empty").get()["ids"] == []


@pytest.mark.unit
class TestDeleteBySourceId:
    """delete_by_source_id only removes the exact content version targeted."""

    def test_removes_only_matching_version(self, store):
        _seed(store, "col")

        store.delete_by_source_id("readme_p_repo_v1", "col")

        ids = store.get_collection("col").get()["ids"]
        assert "readme_p_repo_v1_chunk_0" not in ids
        assert "readme_p_repo_v2_chunk_0" in ids
