"""Tests for hybrid.py — HybridRetriever scoring/blending logic.

These tests document and lock in the scoring formula described in
docs/ARCHITECTURE.md ("Hybrid Retrieval Scoring"):

    blended = vector_weight * vector_norm + keyword_weight * keyword_norm

with per-result-set max-normalization, default weights 0.7 / 0.3, and a
`min_score` cutoff applied before ranking and truncation to `max_chunks`.
"""

import pytest
from unittest.mock import Mock

from rag.retriever.hybrid import HybridRetriever


@pytest.mark.unit
class TestHybridRetrieverScoring:
    """Test suite for HybridRetriever blend/normalize/filter behavior."""

    def _make_retriever(self, vector_results, keyword_results,
                        vector_weight=0.7, keyword_weight=0.3):
        """Build a HybridRetriever with stubbed vector/keyword backends.

        Args:
            vector_results: what VectorStore.query() should return.
            keyword_results: what KeywordSearcher.search() should return.
            vector_weight: vector weight for the blend.
            keyword_weight: keyword weight for the blend.

        Returns:
            A HybridRetriever wired to Mock backends.
        """
        vector_store = Mock()
        vector_store.query.return_value = vector_results
        # _get_all_chunks() reads the whole collection for keyword indexing,
        # but the blend does not use its return value, so an empty collection
        # is sufficient here.
        vector_store.get_collection.return_value.get.return_value = {
            "ids": [], "documents": [], "metadatas": [],
        }

        keyword_searcher = Mock()
        keyword_searcher.search.return_value = keyword_results

        return HybridRetriever(
            vector_store, keyword_searcher,
            vector_weight=vector_weight, keyword_weight=keyword_weight,
        )

    def test_worked_example_matches_documentation(self):
        """Blend, normalization, and ranking match the ARCHITECTURE.md example.

        Chunk A is vector-only, B is in both, C is keyword-only. With defaults
        (0.7 / 0.3) the blended scores are A=0.700, B=0.765, C=0.300, so the
        ranking is B > A > C.
        """
        vector_results = [
            {"id": "A", "score": 0.80, "text": "a", "metadata": {}},
            {"id": "B", "score": 0.60, "text": "b", "metadata": {}},
        ]
        keyword_results = [
            {"id": "C", "bm25_score": 5.0, "text": "c", "metadata": {}},
            {"id": "B", "bm25_score": 4.0, "text": "b", "metadata": {}},
        ]
        retriever = self._make_retriever(vector_results, keyword_results)

        results = retriever.retrieve(
            query="q", profile_id="p", query_embedding=[0.1, 0.2],
        )

        assert [r["id"] for r in results] == ["B", "A", "C"]
        by_id = {r["id"]: r for r in results}
        assert by_id["A"]["score"] == pytest.approx(0.70)
        assert by_id["B"]["score"] == pytest.approx(0.765)
        assert by_id["C"]["score"] == pytest.approx(0.30)

    def test_single_retriever_chunk_gets_zero_for_missing_signal(self):
        """A chunk found by only one retriever scores 0 on the other signal."""
        vector_results = [{"id": "A", "score": 0.5, "text": "a", "metadata": {}}]
        keyword_results = [{"id": "C", "bm25_score": 2.0, "text": "c", "metadata": {}}]
        retriever = self._make_retriever(vector_results, keyword_results)

        results = retriever.retrieve(
            query="q", profile_id="p", query_embedding=[0.1],
        )
        by_id = {r["id"]: r for r in results}

        # A is vector-only: keyword signal is 0, vector normalizes to 1.0 → 0.7.
        assert by_id["A"]["keyword_score"] == 0.0
        assert by_id["A"]["vector_score"] == pytest.approx(1.0)
        assert by_id["A"]["score"] == pytest.approx(0.7)
        # C is keyword-only: vector signal is 0, keyword normalizes to 1.0 → 0.3.
        assert by_id["C"]["vector_score"] == 0.0
        assert by_id["C"]["keyword_score"] == pytest.approx(1.0)
        assert by_id["C"]["score"] == pytest.approx(0.3)

    def test_min_score_cutoff_drops_low_scoring_chunks(self):
        """Chunks whose blended score is below min_score are filtered out."""
        vector_results = [
            {"id": "A", "score": 0.80, "text": "a", "metadata": {}},
            {"id": "B", "score": 0.60, "text": "b", "metadata": {}},
        ]
        keyword_results = [
            {"id": "C", "bm25_score": 5.0, "text": "c", "metadata": {}},
        ]
        retriever = self._make_retriever(vector_results, keyword_results)

        # A=0.700, B=0.525, C=0.300. A cutoff of 0.5 keeps only A and B.
        results = retriever.retrieve(
            query="q", profile_id="p", query_embedding=[0.1], min_score=0.5,
        )

        ids = [r["id"] for r in results]
        assert "C" not in ids
        assert ids == ["A", "B"]

    def test_max_chunks_truncates_to_top_scoring(self):
        """No more than max_chunks results are returned, highest scores first."""
        vector_results = [
            {"id": f"v{i}", "score": 1.0 - i * 0.01, "text": "t", "metadata": {}}
            for i in range(6)
        ]
        retriever = self._make_retriever(vector_results, [])

        results = retriever.retrieve(
            query="q", profile_id="p", query_embedding=[0.1], max_chunks=3,
        )

        assert len(results) == 3
        assert [r["id"] for r in results] == ["v0", "v1", "v2"]

    def test_empty_results_returns_empty_list(self):
        """No candidates from either retriever yields an empty result list."""
        retriever = self._make_retriever([], [])

        results = retriever.retrieve(
            query="q", profile_id="p", query_embedding=[0.1],
        )

        assert results == []

    def test_custom_weights_change_the_blend(self):
        """Non-default weights are applied to the normalized scores."""
        vector_results = [{"id": "A", "score": 0.5, "text": "a", "metadata": {}}]
        keyword_results = [{"id": "A", "bm25_score": 3.0, "text": "a", "metadata": {}}]
        # Both signals normalize to 1.0 (single item per set), so blended
        # equals vector_weight + keyword_weight regardless of raw magnitudes.
        retriever = self._make_retriever(
            vector_results, keyword_results,
            vector_weight=0.4, keyword_weight=0.6,
        )

        results = retriever.retrieve(
            query="q", profile_id="p", query_embedding=[0.1],
        )

        assert results[0]["score"] == pytest.approx(1.0)
        assert results[0]["vector_score"] == pytest.approx(1.0)
        assert results[0]["keyword_score"] == pytest.approx(1.0)
