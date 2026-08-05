"""Tests for vector_store.py"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from rag.retriever.vector_store import VectorStore


@pytest.mark.unit
class TestVectorStoreDeleteCollection:
    """Test suite for VectorStore.delete_collection()."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> VectorStore:
        return VectorStore(persist_dir=str(tmp_path))

    def test_delete_collection_removes_existing_data(self, store: VectorStore) -> None:
        chunk = Mock(
            id="chunk-1", source_id="source-1", chunk_index=0, section="intro", text="hello"
        )
        store.add_chunks([(chunk, [0.1, 0.2, 0.3])], collection_name="profile_abc")

        store.delete_collection("profile_abc")

        # get_collection() re-creates an empty collection since the old one is gone
        remaining = store.get_collection("profile_abc").get(include=["documents"])
        assert remaining["ids"] == []

    def test_delete_collection_tolerates_missing_collection(self, store: VectorStore) -> None:
        """Deleting a collection that was never created must not raise."""
        store.delete_collection("profile_never_ingested")
