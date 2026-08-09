"""Unit tests for LLMReranker and HybridRetriever integration."""

from unittest.mock import MagicMock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.reranker import LLMReranker


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    def test_reranker_scoring_and_sorting(self) -> None:
        """Test scoring and sorting of candidate chunks."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='[{"id": "chunk_1", "score": 0.2}, {"id": "chunk_2", "score": 0.9}]'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        reranker = LLMReranker(client=mock_client)
        chunks = [
            {"id": "chunk_1", "text": "Basic introductory text", "score": 0.8},
            {"id": "chunk_2", "text": "Deep technical relevance", "score": 0.5},
        ]

        reranked = reranker.rerank("technical topic", chunks, top_k=2)

        assert len(reranked) == 2
        # chunk_2 should be first because rerank_score is 0.9
        assert reranked[0]["id"] == "chunk_2"
        assert reranked[0]["rerank_score"] == 0.9
        assert reranked[1]["id"] == "chunk_1"
        assert reranked[1]["rerank_score"] == 0.2

    def test_reranker_fallback_on_exception(self) -> None:
        """Test fallback to initial scores when LLM call fails."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")

        reranker = LLMReranker(client=mock_client)
        chunks = [
            {"id": "chunk_1", "text": "First chunk", "score": 0.9},
            {"id": "chunk_2", "text": "Second chunk", "score": 0.4},
        ]

        scored = reranker.score_chunks("query", chunks)

        assert len(scored) == 2
        assert scored[0]["rerank_score"] == 0.9
        assert scored[1]["rerank_score"] == 0.4

    def test_reranker_parse_markdown_json(self) -> None:
        """Test parsing JSON enclosed inside markdown code fences."""
        raw_text = '```json\n[{"id": "chunk_a", "score": 0.95}]\n```'
        parsed = LLMReranker._parse_scores(raw_text)

        assert len(parsed) == 1
        assert parsed[0]["id"] == "chunk_a"
        assert parsed[0]["score"] == 0.95

    def test_reranker_empty_chunks(self) -> None:
        """Test reranking empty candidate list."""
        reranker = LLMReranker(api_key="test-key")
        result = reranker.rerank("query", [], top_k=5)
        assert result == []

    def test_reranker_no_client(self) -> None:
        """Test behavior when no LLM client is provided."""
        reranker = LLMReranker()
        chunks = [{"id": "c1", "text": "Sample text", "score": 0.7}]
        scored = reranker.score_chunks("query", chunks)
        assert scored[0]["rerank_score"] == 0.7


@pytest.mark.unit
class TestHybridRetrieverWithReranker:
    """Test integration of LLMReranker with HybridRetriever."""

    def test_hybrid_retriever_calls_reranker(self) -> None:
        """Test that HybridRetriever executes 2nd-stage reranking when reranker is set."""
        mock_vector_store = MagicMock()
        mock_keyword_searcher = MagicMock()
        mock_reranker = MagicMock()

        mock_vector_store.query.return_value = [
            {"id": "chunk_1", "score": 0.8, "text": "Vector text 1"},
            {"id": "chunk_2", "score": 0.6, "text": "Vector text 2"},
        ]
        mock_keyword_searcher.search.return_value = [
            {"id": "chunk_1", "bm25_score": 5.0, "text": "Vector text 1"},
        ]

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["chunk_1", "chunk_2"],
            "documents": ["Vector text 1", "Vector text 2"],
            "metadatas": [{}, {}],
        }
        mock_vector_store.get_collection.return_value = mock_collection

        mock_reranker.rerank.return_value = [
            {"id": "chunk_2", "score": 0.6, "rerank_score": 0.95, "text": "Vector text 2"},
            {"id": "chunk_1", "score": 0.8, "rerank_score": 0.3, "text": "Vector text 1"},
        ]

        retriever = HybridRetriever(
            vector_store=mock_vector_store,
            keyword_searcher=mock_keyword_searcher,
            reranker=mock_reranker,
        )

        results = retriever.retrieve(
            query="test query",
            profile_id="123",
            query_embedding=[0.1, 0.2],
            max_chunks=2,
            min_score=0.1,
        )

        assert mock_reranker.rerank.called
        assert len(results) == 2
        assert results[0]["id"] == "chunk_2"
