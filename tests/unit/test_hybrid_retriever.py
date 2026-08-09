"""Tests for hybrid.py"""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.reranker import MockReranker


@pytest.mark.unit
class TestHybridRetrieverReranking:
    """Test suite for HybridRetriever's optional re-ranking step."""

    def _make_retriever(self, reranker=None, rerank_candidates=25):
        vector_store = Mock()
        vector_store.query.return_value = [
            {"id": "a", "text": "python programming", "metadata": {}, "score": 0.9},
            {"id": "b", "text": "unrelated java content", "metadata": {}, "score": 0.5},
        ]
        vector_store.get_collection.return_value = Mock(
            get=Mock(return_value={"ids": [], "documents": [], "metadatas": []})
        )

        keyword_searcher = Mock()
        keyword_searcher.search.return_value = []

        return HybridRetriever(
            vector_store,
            keyword_searcher,
            reranker=reranker,
            rerank_candidates=rerank_candidates,
        )

    def test_without_reranker_preserves_blended_order(self):
        retriever = self._make_retriever(reranker=None)

        results = retriever.retrieve(
            "python programming", "profile1", [0.1] * 3, max_chunks=10, min_score=0.0
        )

        assert [r["id"] for r in results] == ["a", "b"]
        assert "rerank_score" not in results[0]

    def test_with_reranker_reorders_by_relevance(self):
        retriever = self._make_retriever(reranker=MockReranker())

        results = retriever.retrieve("java", "profile1", [0.1] * 3, max_chunks=10, min_score=0.0)

        assert results[0]["id"] == "b"
        assert "rerank_score" in results[0]

    def test_reranker_not_called_on_empty_results(self):
        reranker = Mock()
        retriever = self._make_retriever(reranker=reranker)
        retriever.vector_store.query.return_value = []
        retriever.vector_store.get_collection.return_value = Mock(
            get=Mock(return_value={"ids": [], "documents": [], "metadatas": []})
        )

        results = retriever.retrieve("python", "profile1", [0.1] * 3, max_chunks=10, min_score=0.9)

        assert results == []
        reranker.rerank.assert_not_called()

    def test_rerank_candidates_limits_reranked_set(self):
        reranker = Mock()
        reranker.rerank.side_effect = lambda query, chunks: chunks

        retriever = self._make_retriever(reranker=reranker, rerank_candidates=1)

        retriever.retrieve("python", "profile1", [0.1] * 3, max_chunks=10, min_score=0.0)

        called_chunks = reranker.rerank.call_args[0][1]
        assert len(called_chunks) == 1
