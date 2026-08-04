"""Tests for vector_store.py, in particular the cosine distance -> similarity conversion."""

from unittest.mock import MagicMock, patch

import pytest

from rag.retriever.vector_store import VectorStore


def _chroma_query_response(distances: list[float]) -> dict:
    """Build a ChromaDB-shaped query response for the given distances."""
    n = len(distances)
    return {
        "documents": [[f"chunk text {i}" for i in range(n)]],
        "metadatas": [[{"source_id": f"source-{i}"} for i in range(n)]],
        "distances": [distances],
        "ids": [[f"id-{i}" for i in range(n)]],
    }


@pytest.mark.unit
class TestVectorStoreQuery:
    """Test suite for VectorStore.query()'s cosine similarity conversion."""

    @pytest.fixture
    def vector_store(self) -> VectorStore:
        """Create a VectorStore with the real ChromaDB client patched out."""
        with patch("rag.retriever.vector_store.chromadb.PersistentClient"):
            store = VectorStore(persist_dir="unused")
        return store

    @staticmethod
    def _with_collection(vector_store: VectorStore, distances: list[float]) -> MagicMock:
        """Wire up vector_store.get_collection() to return a mock collection."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = _chroma_query_response(distances)
        vector_store.get_collection = MagicMock(return_value=mock_collection)  # type: ignore[method-assign]
        return mock_collection

    def test_zero_distance_gives_similarity_one(self, vector_store: VectorStore) -> None:
        """Identical embeddings (cosine distance 0) should score a perfect 1.0."""
        self._with_collection(vector_store, [0.0])

        results = vector_store.query([0.1] * 5, "profile_1")

        assert results[0]["score"] == 1.0

    def test_distance_one_gives_similarity_zero(self, vector_store: VectorStore) -> None:
        """Orthogonal embeddings (cosine distance 1) should score 0.0."""
        self._with_collection(vector_store, [1.0])

        results = vector_store.query([0.1] * 5, "profile_1")

        assert results[0]["score"] == 0.0

    def test_distance_greater_than_one_clamps_to_zero(self, vector_store: VectorStore) -> None:
        """Opposite-direction embeddings (cosine distance > 1) must clamp, not go negative."""
        self._with_collection(vector_store, [1.6])

        results = vector_store.query([0.1] * 5, "profile_1")

        assert results[0]["score"] == 0.0

    def test_typical_distance_produces_expected_similarity(self, vector_store: VectorStore) -> None:
        """Matches the worked example in docs/ARCHITECTURE.md: distance 0.35 -> similarity 0.65."""
        self._with_collection(vector_store, [0.35])

        results = vector_store.query([0.1] * 5, "profile_1")

        assert results[0]["score"] == pytest.approx(0.65)

    def test_multiple_results_preserve_order_and_scores(self, vector_store: VectorStore) -> None:
        """Scores should map 1:1 to their distances, in the order ChromaDB returned them."""
        self._with_collection(vector_store, [0.2, 0.5, 0.8])

        results = vector_store.query([0.1] * 5, "profile_1", n_results=3)

        scores = [r["score"] for r in results]
        assert scores == pytest.approx([0.8, 0.5, 0.2])

    def test_empty_results_returns_empty_list(self, vector_store: VectorStore) -> None:
        """No matches should return an empty list, not raise."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]],
        }
        vector_store.get_collection = MagicMock(return_value=mock_collection)  # type: ignore[method-assign]

        results = vector_store.query([0.1] * 5, "profile_1")

        assert results == []

    def test_result_shape(self, vector_store: VectorStore) -> None:
        """Each result dict should carry id, text, metadata, and score."""
        self._with_collection(vector_store, [0.4])

        results = vector_store.query([0.1] * 5, "profile_1")

        assert len(results) == 1
        result = results[0]
        assert result["id"] == "id-0"
        assert result["text"] == "chunk text 0"
        assert result["metadata"] == {"source_id": "source-0"}
        assert result["score"] == pytest.approx(0.6)
