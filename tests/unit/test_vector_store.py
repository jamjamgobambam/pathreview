"""Tests for vector_store.py

These tests pin down two things that the architecture doc now documents:
1. Collections use cosine distance (``hnsw:space="cosine"``), NOT Euclidean.
2. ChromaDB distances are converted to a similarity via ``1 / (1 + distance)``.
"""

from dataclasses import dataclass

import pytest

from rag.retriever.vector_store import VectorStore


@dataclass
class FakeChunk:
    """Minimal chunk with the fields VectorStore.add_chunks reads."""

    id: str
    source_id: str
    chunk_index: int
    text: str
    section: str = ""


@pytest.mark.unit
class TestVectorStore:
    """Test suite for VectorStore cosine similarity behavior."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a VectorStore backed by a temporary on-disk directory."""
        return VectorStore(persist_dir=str(tmp_path / "chroma"))

    def _add(self, store, collection, items):
        """Add ``items`` (id -> embedding) as chunks to ``collection``."""
        chunks = [
            (FakeChunk(id=cid, source_id="src", chunk_index=i, text=f"doc {cid}"), emb)
            for i, (cid, emb) in enumerate(items.items())
        ]
        store.add_chunks(chunks, collection)

    def test_collection_created_with_cosine_space(self, store):
        """Collections are created with hnsw:space=cosine, not the l2 default."""
        collection = store.get_collection("profile_cosine")
        assert collection.metadata["hnsw:space"] == "cosine"

    def test_identical_direction_scores_one(self, store):
        """A vector identical to the query has cosine distance 0 -> similarity 1.0."""
        self._add(store, "col1", {"a": [1.0, 0.0, 0.0]})
        results = store.query([1.0, 0.0, 0.0], "col1", n_results=1)

        assert len(results) == 1
        assert results[0]["id"] == "a"
        assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)

    def test_similarity_is_magnitude_invariant(self, store):
        """Cosine ignores magnitude: [2,0,0] matches query [1,0,0] with similarity 1.0.

        This is the decisive check that the metric is cosine, not Euclidean.
        Under Euclidean distance the distance would be 1.0 (score 0.5), not 0.0.
        """
        self._add(store, "col2", {"scaled": [2.0, 0.0, 0.0]})
        results = store.query([1.0, 0.0, 0.0], "col2", n_results=1)

        assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)

    def test_orthogonal_vector_scores_half(self, store):
        """An orthogonal vector has cosine distance 1 -> similarity 1/(1+1) = 0.5."""
        self._add(store, "col3", {"ortho": [0.0, 1.0, 0.0]})
        results = store.query([1.0, 0.0, 0.0], "col3", n_results=1)

        assert results[0]["score"] == pytest.approx(0.5, abs=1e-4)

    def test_opposite_vector_scores_one_third(self, store):
        """An opposite vector has cosine distance 2 -> similarity 1/(1+2) = 1/3."""
        self._add(store, "col4", {"opp": [-1.0, 0.0, 0.0]})
        results = store.query([1.0, 0.0, 0.0], "col4", n_results=1)

        assert results[0]["score"] == pytest.approx(1.0 / 3.0, abs=1e-4)

    def test_scores_bounded_and_descending(self, store):
        """Similarities stay in (0, 1] and rank closer directions higher."""
        self._add(
            store,
            "col5",
            {
                "same": [1.0, 0.0, 0.0],
                "ortho": [0.0, 1.0, 0.0],
                "opp": [-1.0, 0.0, 0.0],
            },
        )
        results = store.query([1.0, 0.0, 0.0], "col5", n_results=3)

        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert all(0.0 < s <= 1.0 for s in scores)
        assert results[0]["id"] == "same"

    def test_query_empty_collection_returns_empty(self, store):
        """Querying a collection with no chunks returns an empty list."""
        store.get_collection("empty")
        results = store.query([1.0, 0.0, 0.0], "empty", n_results=5)

        assert results == []

    def test_query_result_shape(self, store):
        """Each result carries id, text, metadata, and score."""
        self._add(store, "col6", {"a": [1.0, 0.0, 0.0]})
        result = store.query([1.0, 0.0, 0.0], "col6", n_results=1)[0]

        assert set(result) == {"id", "text", "metadata", "score"}
        assert result["metadata"]["source_id"] == "src"

    def test_delete_by_source_id(self, store):
        """Deleting by source_id removes that source's chunks."""
        self._add(store, "col7", {"a": [1.0, 0.0, 0.0], "b": [0.0, 1.0, 0.0]})
        store.delete_by_source_id("src", "col7")

        results = store.query([1.0, 0.0, 0.0], "col7", n_results=5)
        assert results == []
