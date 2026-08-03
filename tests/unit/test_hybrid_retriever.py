"""Tests for HybridRetriever re-ranking wiring (issue #34).

Focus: the optional LLM re-ranking path. When re-ranking is disabled (the
default) the retriever must behave exactly as before.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever, build_hybrid_retriever
from rag.retriever.reranker import LLMReranker


@pytest.mark.unit
class TestHybridRetrieverReranking:
    """Test suite for the re-ranking flag on HybridRetriever.retrieve()."""

    @pytest.fixture
    def vector_store(self):
        """Mock vector store returning three ranked chunks."""
        store = Mock()
        store.query.return_value = [
            {"id": "c1", "score": 0.9, "text": "chunk one", "metadata": {}},
            {"id": "c2", "score": 0.8, "text": "chunk two", "metadata": {}},
            {"id": "c3", "score": 0.7, "text": "chunk three", "metadata": {}},
        ]
        collection = Mock()
        collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        store.get_collection.return_value = collection
        return store

    @pytest.fixture
    def keyword_searcher(self):
        """Mock keyword searcher returning no keyword hits."""
        searcher = Mock()
        searcher.search.return_value = []
        return searcher

    def test_disabled_path_does_not_call_reranker(self, vector_store, keyword_searcher):
        """With rerank=False, the reranker is never invoked and order is by score."""
        reranker = Mock()
        retriever = HybridRetriever(vector_store, keyword_searcher, reranker=reranker)

        results = retriever.retrieve(
            "query", "p1", [0.1, 0.2], max_chunks=3, min_score=0.0, rerank=False
        )

        reranker.rerank.assert_not_called()
        assert [r["id"] for r in results] == ["c1", "c2", "c3"]

    def test_enabled_path_uses_reranker_order(self, vector_store, keyword_searcher):
        """With rerank=True, the retriever returns the reranker's ordering."""
        reranker = Mock()
        reranker.rerank.return_value = [{"id": "c3"}, {"id": "c1"}, {"id": "c2"}]
        retriever = HybridRetriever(vector_store, keyword_searcher, reranker=reranker)

        results = retriever.retrieve(
            "query", "p1", [0.1, 0.2], max_chunks=3, min_score=0.0, rerank=True
        )

        reranker.rerank.assert_called_once()
        assert [r["id"] for r in results] == ["c3", "c1", "c2"]

    def test_enabled_without_reranker_falls_back(self, vector_store, keyword_searcher):
        """rerank=True but no reranker configured → unchanged hybrid order."""
        retriever = HybridRetriever(vector_store, keyword_searcher, reranker=None)

        results = retriever.retrieve(
            "query", "p1", [0.1, 0.2], max_chunks=3, min_score=0.0, rerank=True
        )

        assert [r["id"] for r in results] == ["c1", "c2", "c3"]

    def test_reranker_receives_candidate_pool(self, vector_store, keyword_searcher):
        """The reranker is asked to return top_k == max_chunks."""
        reranker = Mock()
        reranker.rerank.return_value = []
        retriever = HybridRetriever(vector_store, keyword_searcher, reranker=reranker)

        retriever.retrieve("query", "p1", [0.1, 0.2], max_chunks=2, min_score=0.0, rerank=True)

        _, kwargs = reranker.rerank.call_args
        assert kwargs.get("top_k") == 2

    def test_rerank_widens_candidate_fetch(self, vector_store, keyword_searcher):
        """With rerank=True the actual fetch grows to max_chunks * multiplier."""
        reranker = Mock()
        reranker.rerank.return_value = []
        retriever = HybridRetriever(
            vector_store, keyword_searcher, reranker=reranker, rerank_candidate_multiplier=3
        )

        retriever.retrieve("query", "p1", [0.1, 0.2], max_chunks=4, min_score=0.0, rerank=True)

        _, kwargs = vector_store.query.call_args
        assert kwargs["n_results"] == 12  # 4 * 3, not the default 4 * 2
        keyword_searcher.search.assert_called_with("query", top_k=12)

    def test_disabled_fetch_is_unchanged(self, vector_store, keyword_searcher):
        """With rerank=False the fetch stays at the original max_chunks * 2."""
        retriever = HybridRetriever(
            vector_store, keyword_searcher, reranker=Mock(), rerank_candidate_multiplier=3
        )

        retriever.retrieve("query", "p1", [0.1, 0.2], max_chunks=4, min_score=0.0, rerank=False)

        _, kwargs = vector_store.query.call_args
        assert kwargs["n_results"] == 8  # 4 * 2, unchanged


@pytest.mark.unit
class TestBuildHybridRetriever:
    """Test suite for the settings-driven build_hybrid_retriever factory."""

    def test_disabled_attaches_no_reranker(self):
        """enable_reranking=False -> no reranker, multiplier passed through."""
        settings = SimpleNamespace(
            enable_reranking=False,
            rerank_model="m",
            rerank_candidate_multiplier=4,
            openrouter_api_key="k",
            openrouter_base_url="http://example",
        )

        retriever = build_hybrid_retriever(Mock(), Mock(), settings)

        assert retriever.reranker is None
        assert retriever.rerank_candidate_multiplier == 4

    def test_enabled_attaches_reranker_from_settings(self):
        """enable_reranking=True -> reranker built from settings."""
        settings = SimpleNamespace(
            enable_reranking=True,
            rerank_model="my/rerank-model",
            rerank_candidate_multiplier=5,
            openrouter_api_key="k",
            openrouter_base_url="http://example",
        )

        retriever = build_hybrid_retriever(Mock(), Mock(), settings, client=Mock())

        assert isinstance(retriever.reranker, LLMReranker)
        assert retriever.reranker.model == "my/rerank-model"
        assert retriever.rerank_candidate_multiplier == 5
