"""Tests for hybrid.py

These pin down the hybrid scoring formula documented in ARCHITECTURE.md:
per-signal max-normalization, the weighted blend (default 0.7 vector / 0.3
keyword), the min_score threshold, and top-max_chunks ranking.
"""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever


def _make_retriever(vector_results, keyword_results, **kwargs):
    """Build a HybridRetriever with mocked vector and keyword backends."""
    vector_store = Mock()
    vector_store.query.return_value = vector_results
    # _get_all_chunks() reads get_collection(...).get(...); value is unused by the blend.
    vector_store.get_collection.return_value.get.return_value = {
        "ids": [],
        "documents": [],
        "metadatas": [],
    }

    keyword_searcher = Mock()
    keyword_searcher.search.return_value = keyword_results

    return HybridRetriever(vector_store, keyword_searcher, **kwargs)


def _vec(chunk_id, score):
    return {"id": chunk_id, "text": f"text {chunk_id}", "metadata": {}, "score": score}


def _kw(chunk_id, bm25):
    return {"id": chunk_id, "text": f"text {chunk_id}", "metadata": {}, "bm25_score": bm25}


@pytest.mark.unit
class TestHybridRetriever:
    """Test suite for HybridRetriever scoring."""

    def test_weighted_blend_default_weights(self):
        """blended = 0.7*vector_norm + 0.3*keyword_norm over normalized scores.

        vector max = 1.0, keyword max = 4.0.
          a: 0.7*(1.0/1.0) + 0.3*(2.0/4.0) = 0.85
          b: 0.7*(0.5/1.0) + 0.3*(4.0/4.0) = 0.65
        """
        retriever = _make_retriever(
            [_vec("a", 1.0), _vec("b", 0.5)],
            [_kw("a", 2.0), _kw("b", 4.0)],
        )
        results = retriever.retrieve("q", "p1", [0.1, 0.2], max_chunks=10, min_score=0.0)

        by_id = {r["id"]: r for r in results}
        assert by_id["a"]["score"] == pytest.approx(0.85)
        assert by_id["b"]["score"] == pytest.approx(0.65)
        # Higher blended score ranks first.
        assert [r["id"] for r in results] == ["a", "b"]

    def test_custom_weights(self):
        """Constructor weights override the 0.7/0.3 defaults."""
        retriever = _make_retriever(
            [_vec("a", 1.0)],
            [_kw("a", 4.0)],
            vector_weight=0.5,
            keyword_weight=0.5,
        )
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=0.0)

        # Single result in each signal -> both norms are 1.0 -> 0.5 + 0.5 = 1.0.
        assert results[0]["score"] == pytest.approx(1.0)

    def test_min_score_filters_low_results(self):
        """Chunks below min_score are dropped."""
        retriever = _make_retriever(
            [_vec("a", 1.0), _vec("b", 0.5)],
            [_kw("a", 2.0), _kw("b", 4.0)],
        )
        # a scores 0.85, b scores 0.65; threshold 0.7 keeps only a.
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=0.7)

        assert [r["id"] for r in results] == ["a"]

    def test_all_below_threshold_returns_empty(self):
        """If every blended score is below min_score, the result list is empty."""
        retriever = _make_retriever([_vec("a", 1.0)], [_kw("a", 1.0)])
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=1.5)

        assert results == []

    def test_chunk_in_only_one_signal(self):
        """The result set is the union of both signals; a missing signal scores 0.

        a is vector-only: 0.7*1.0 + 0.3*0 = 0.7
        b is keyword-only: 0.7*0 + 0.3*1.0 = 0.3
        """
        retriever = _make_retriever([_vec("a", 1.0)], [_kw("b", 5.0)])
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=0.0)

        by_id = {r["id"]: r for r in results}
        assert by_id["a"]["score"] == pytest.approx(0.7)
        assert by_id["a"]["keyword_score"] == pytest.approx(0.0)
        assert by_id["b"]["score"] == pytest.approx(0.3)
        assert by_id["b"]["vector_score"] == pytest.approx(0.0)

    def test_falls_back_to_vector_when_keyword_empty(self):
        """With no keyword results, blended score is vector_weight * vector_norm."""
        retriever = _make_retriever([_vec("a", 1.0), _vec("b", 0.5)], [])
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=0.0)

        by_id = {r["id"]: r for r in results}
        assert by_id["a"]["score"] == pytest.approx(0.7)
        assert by_id["b"]["score"] == pytest.approx(0.35)

    def test_max_chunks_limits_results(self):
        """No more than max_chunks results are returned."""
        vec = [_vec(str(i), 1.0 - i * 0.05) for i in range(10)]
        retriever = _make_retriever(vec, [])
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=3, min_score=0.0)

        assert len(results) == 3

    def test_results_expose_component_scores(self):
        """Each result exposes its vector_score and keyword_score components."""
        retriever = _make_retriever([_vec("a", 1.0)], [_kw("a", 4.0)])
        result = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=0.0)[0]

        assert set(result) >= {"id", "text", "metadata", "score", "vector_score", "keyword_score"}

    def test_no_results_returns_empty(self):
        """No vector or keyword hits yields an empty list."""
        retriever = _make_retriever([], [])
        results = retriever.retrieve("q", "p1", [0.1], max_chunks=10, min_score=0.0)

        assert results == []
