"""Tests for VectorStore."""

from unittest.mock import MagicMock, patch

import pytest

from rag.retriever.vector_store import VectorStore


@pytest.mark.unit
class TestVectorStoreDeleteCollection:
    """Tests for VectorStore.delete_collection."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Return a mock chromadb client."""
        return MagicMock()

    @pytest.fixture
    def vector_store(self, mock_client: MagicMock) -> VectorStore:
        """Return a VectorStore backed by a mock chromadb client."""
        with patch("chromadb.PersistentClient", return_value=mock_client):
            return VectorStore()

    def test_delete_collection_calls_client(
        self, vector_store: VectorStore, mock_client: MagicMock
    ) -> None:
        """delete_collection delegates to the underlying chromadb client."""
        vector_store.delete_collection("profile_abc123")

        mock_client.delete_collection.assert_called_once_with(name="profile_abc123")

    def test_delete_collection_no_op_when_collection_missing(
        self, vector_store: VectorStore, mock_client: MagicMock
    ) -> None:
        """delete_collection silently succeeds when the collection doesn't exist.

        Profiles may be deleted before any content is ingested, so a missing
        collection is an expected condition, not an error.
        """
        mock_client.delete_collection.side_effect = ValueError("Collection not found")

        vector_store.delete_collection("profile_abc123")  # must not raise

        mock_client.delete_collection.assert_called_once_with(name="profile_abc123")
