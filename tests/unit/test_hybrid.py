"""Tests for hybrid.py"""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever


@pytest.mark.unit
class TestHybridRetrieverReranking:
    """Test suite for HybridRetriever's optional re-ranking behavior."""

    @pytest.fixture
    def mock_vector_store(self) -> Mock:
        """Create a mock vector store returning two candidate chunks."""
        store = Mock()
        collection = Mock()
        collection.get.return_value = {
            "ids": ["a", "b"],
            "documents": ["chunk a text", "chunk b text"],
            "metadatas": [{}, {}],
        }
        store.get_collection.return_value = collection
        store.query.return_value = [
            {"id": "a", "score": 0.9, "text": "chunk a text", "metadata": {}},
            {"id": "b", "score": 0.6, "text": "chunk b text", "metadata": {}},
        ]
        return store

    @pytest.fixture
    def mock_keyword_searcher(self) -> Mock:
        """Create a mock keyword searcher returning no results."""
        searcher = Mock()
        searcher.search.return_value = []
        return searcher

    @pytest.fixture
    def mock_reranker(self) -> Mock:
        """Create a mock LLMReranker."""
        reranker = Mock()
        reranker.rerank.return_value = [
            {
                "id": "b",
                "text": "chunk b text",
                "metadata": {},
                "score": 0.6,
                "llm_score": 0.95,
            },
            {
                "id": "a",
                "text": "chunk a text",
                "metadata": {},
                "score": 0.9,
                "llm_score": 0.1,
            },
        ]
        return reranker

    def test_reranker_not_called_by_default(
        self, mock_vector_store: Mock, mock_keyword_searcher: Mock, mock_reranker: Mock
    ) -> None:
        """Test that retrieve() does not call the reranker unless use_reranker=True."""
        retriever = HybridRetriever(
            mock_vector_store, mock_keyword_searcher, reranker=mock_reranker
        )

        retriever.retrieve("query", "profile1", [0.1, 0.2], min_score=0.0)

        mock_reranker.rerank.assert_not_called()

    def test_reranker_not_called_when_none_configured(
        self, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that use_reranker=True has no effect if no reranker was provided."""
        retriever = HybridRetriever(mock_vector_store, mock_keyword_searcher, reranker=None)

        result = retriever.retrieve(
            "query", "profile1", [0.1, 0.2], min_score=0.0, use_reranker=True
        )

        assert isinstance(result, list)

    def test_reranker_called_when_enabled_and_configured(
        self, mock_vector_store: Mock, mock_keyword_searcher: Mock, mock_reranker: Mock
    ) -> None:
        """Test that retrieve() calls the reranker when enabled and configured."""
        retriever = HybridRetriever(
            mock_vector_store, mock_keyword_searcher, reranker=mock_reranker
        )

        result = retriever.retrieve(
            "query", "profile1", [0.1, 0.2], min_score=0.0, use_reranker=True
        )

        mock_reranker.rerank.assert_called_once()
        assert result[0]["id"] == "b"
        assert result[0]["llm_score"] == 0.95

    def test_reranker_receives_query_and_blended_results(
        self, mock_vector_store: Mock, mock_keyword_searcher: Mock, mock_reranker: Mock
    ) -> None:
        """Test that the reranker is called with the query and blended chunk list."""
        retriever = HybridRetriever(
            mock_vector_store, mock_keyword_searcher, reranker=mock_reranker
        )

        retriever.retrieve(
            "my query text",
            "profile1",
            [0.1, 0.2],
            max_chunks=5,
            min_score=0.0,
            use_reranker=True,
        )

        call_args = mock_reranker.rerank.call_args
        assert call_args[0][0] == "my query text"
        assert isinstance(call_args[0][1], list)
        assert call_args[0][2] == 5

    def test_existing_behavior_unchanged_without_reranker(
        self, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that retrieve() output shape is unchanged with no reranker (backward compat)."""
        retriever = HybridRetriever(mock_vector_store, mock_keyword_searcher)

        result = retriever.retrieve("query", "profile1", [0.1, 0.2], min_score=0.0)

        expected_keys = {"id", "text", "metadata", "score", "vector_score", "keyword_score"}
        assert all(expected_keys.issubset(r.keys()) for r in result)
        assert "llm_score" not in result[0]
