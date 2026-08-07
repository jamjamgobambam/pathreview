"""Tests for hybrid.py

Reproduction test for issue #36: docs/ARCHITECTURE.md does not explain the
hybrid retrieval scoring formula. This test demonstrates the actual blending
behavior by hand-calculating expected scores and confirming the implementation
matches, since no doc currently describes this formula.
"""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever


def _mock_empty_collection() -> Mock:
    """Build a mock collection whose get() returns empty lists, matching the
    shape _get_all_chunks() expects."""
    return Mock(get=Mock(return_value={"ids": [], "documents": [], "metadatas": []}))


@pytest.mark.unit
class TestHybridRetrieverScoringFormula:
    """Reproduction tests for issue #36 - undocumented scoring formula."""

    @pytest.fixture
    def retriever(self) -> HybridRetriever:
        """Create a HybridRetriever with default weights (0.7 vector / 0.3 keyword)."""
        vector_store = Mock()
        keyword_searcher = Mock()
        return HybridRetriever(vector_store, keyword_searcher)

    def test_default_weights_are_07_vector_03_keyword(self, retriever: HybridRetriever) -> None:
        """Confirms the default weights. These defaults are not documented
        anywhere in docs/ARCHITECTURE.md."""
        assert retriever.vector_weight == 0.7
        assert retriever.keyword_weight == 0.3

    def test_blended_score_matches_hand_calculated_formula(
        self, retriever: HybridRetriever
    ) -> None:
        """Reproduction: constructs a known set of vector + keyword results and
        confirms the blended score matches manual calculation using the
        formula: blended = (vector_weight * normalized_vector_score) +
        (keyword_weight * normalized_keyword_score), where each score is
        normalized by dividing by the max score in its own result set.
        """
        retriever.vector_store.query = Mock(  # type: ignore[method-assign]
            return_value=[
                {"id": "A", "score": 0.9, "text": "chunk a", "metadata": {}},
                {"id": "B", "score": 0.6, "text": "chunk b", "metadata": {}},
                {"id": "C", "score": 0.3, "text": "chunk c", "metadata": {}},
            ]
        )
        retriever.vector_store.get_collection = Mock(  # type: ignore[method-assign]
            return_value=_mock_empty_collection()
        )
        retriever.keyword_searcher.search = Mock(  # type: ignore[method-assign]
            return_value=[
                {"id": "B", "bm25_score": 5.0, "text": "chunk b"},
                {"id": "C", "bm25_score": 2.0, "text": "chunk c"},
                {"id": "D", "bm25_score": 1.0, "text": "chunk d"},
            ]
        )

        results = retriever.retrieve(
            query="test query",
            profile_id="p1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=10,
            min_score=0.3,
        )

        scores_by_id = {r["id"]: r["score"] for r in results}

        assert "D" not in scores_by_id

        assert scores_by_id["A"] == pytest.approx(0.700, abs=0.001)
        assert scores_by_id["B"] == pytest.approx(0.767, abs=0.001)
        assert scores_by_id["C"] == pytest.approx(0.353, abs=0.001)

        result_ids = [r["id"] for r in results]
        assert result_ids == ["B", "A", "C"]

    def test_normalization_is_per_result_set_not_global(self, retriever: HybridRetriever) -> None:
        """Reproduction: demonstrates that normalization divides each score by
        the max score within its OWN result set (vector max, keyword max
        separately), not a single global max across both sets."""
        retriever.vector_store.query = Mock(  # type: ignore[method-assign]
            return_value=[
                {"id": "X", "score": 0.5, "text": "chunk x", "metadata": {}},
            ]
        )
        retriever.vector_store.get_collection = Mock(  # type: ignore[method-assign]
            return_value=_mock_empty_collection()
        )
        retriever.keyword_searcher.search = Mock(return_value=[])  # type: ignore[method-assign]

        results = retriever.retrieve(
            query="test query",
            profile_id="p1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=10,
            min_score=0.0,
        )

        assert results[0]["score"] == pytest.approx(0.7, abs=0.001)

    def test_chunk_only_needs_to_appear_in_one_result_set(self, retriever: HybridRetriever) -> None:
        """Reproduction: confirms chunks are unioned across vector and keyword
        result sets - a chunk appearing in only one set still gets a blended
        score (with the missing side treated as 0)."""
        retriever.vector_store.query = Mock(  # type: ignore[method-assign]
            return_value=[
                {"id": "vector_only", "score": 0.8, "text": "v", "metadata": {}},
            ]
        )
        retriever.vector_store.get_collection = Mock(  # type: ignore[method-assign]
            return_value=_mock_empty_collection()
        )
        retriever.keyword_searcher.search = Mock(  # type: ignore[method-assign]
            return_value=[
                {"id": "keyword_only", "bm25_score": 3.0, "text": "k"},
            ]
        )

        results = retriever.retrieve(
            query="test query",
            profile_id="p1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=10,
            min_score=0.0,
        )

        result_ids = {r["id"] for r in results}
        assert "vector_only" in result_ids
        assert "keyword_only" in result_ids
