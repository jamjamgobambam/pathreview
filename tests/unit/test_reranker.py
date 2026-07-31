"""Tests for the LLM-based chunk re-ranker (issue #34)."""

from unittest.mock import Mock

import pytest

from rag.retriever.reranker import LLMReranker


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    @pytest.fixture
    def candidate_chunks(self):
        """Chunks as produced by HybridRetriever.retrieve().

        The hybrid ordering intentionally puts the LESS relevant chunk first,
        so a working re-ranker must be able to change the order.
        """
        return [
            {"id": "c1", "text": "generic filler about the weather", "score": 0.91},
            {"id": "c2", "text": "built a RAG pipeline with hybrid retrieval", "score": 0.88},
            {"id": "c3", "text": "list of hobbies and interests", "score": 0.85},
        ]

    @pytest.fixture
    def mock_client(self):
        """A mocked OpenAI-style client."""
        return Mock()

    def test_reorders_by_llm_scores(self, mock_client, candidate_chunks):
        """When enabled, chunks are reordered by LLM relevance, not hybrid score."""
        reranker = LLMReranker(client=mock_client, model="test-model")
        reranker._score_chunk = Mock(
            side_effect=lambda q, c: {"c1": 0.1, "c2": 0.95, "c3": 0.2}[c["id"]]
        )

        result = reranker.rerank("experience building RAG systems", candidate_chunks, top_k=3)

        assert [c["id"] for c in result] == ["c2", "c3", "c1"]

    def test_attaches_rerank_score_and_preserves_original(self, mock_client, candidate_chunks):
        """Each result gains a rerank_score; the original hybrid score stays."""
        reranker = LLMReranker(client=mock_client, model="test-model")
        reranker._score_chunk = Mock(return_value=0.5)

        result = reranker.rerank("query", candidate_chunks, top_k=3)

        assert all("rerank_score" in c for c in result)
        assert all("score" in c for c in result)

    def test_top_k_limits_output(self, mock_client, candidate_chunks):
        """rerank() returns at most top_k chunks."""
        reranker = LLMReranker(client=mock_client, model="test-model")
        reranker._score_chunk = Mock(return_value=0.5)

        result = reranker.rerank("query", candidate_chunks, top_k=2)

        assert len(result) == 2

    def test_empty_candidates_returns_empty(self, mock_client):
        """No candidates in, no candidates out — and no LLM calls."""
        reranker = LLMReranker(client=mock_client, model="test-model")

        result = reranker.rerank("query", [], top_k=5)

        assert result == []
        mock_client.chat.completions.create.assert_not_called()

    def test_llm_failure_falls_back_to_hybrid_order(self, mock_client, candidate_chunks):
        """If the LLM call raises, preserve the original hybrid ordering."""
        reranker = LLMReranker(client=mock_client, model="test-model")
        reranker._score_chunk = Mock(side_effect=RuntimeError("LLM down"))

        result = reranker.rerank("query", candidate_chunks, top_k=3)

        assert [c["id"] for c in result] == ["c1", "c2", "c3"]

    def test_ties_keep_original_order(self, mock_client, candidate_chunks):
        """Equal scores preserve the incoming hybrid order (deterministic)."""
        reranker = LLMReranker(client=mock_client, model="test-model")
        reranker._score_chunk = Mock(return_value=0.7)

        result = reranker.rerank("query", candidate_chunks, top_k=3)

        assert [c["id"] for c in result] == ["c1", "c2", "c3"]

    def test_parse_score_extracts_number(self, mock_client):
        """_parse_score pulls a float out of noisy LLM text."""
        reranker = LLMReranker(client=mock_client, model="test-model")

        assert reranker._parse_score("0.83") == 0.83
        assert reranker._parse_score("Relevance: 0.4 (fairly)") == 0.4

    def test_parse_score_clamps_and_defaults(self, mock_client):
        """Out-of-range values clamp to [0, 1]; garbage defaults to 0.0."""
        reranker = LLMReranker(client=mock_client, model="test-model")

        assert reranker._parse_score("1.9") == 1.0
        assert reranker._parse_score("no number here") == 0.0
        assert reranker._parse_score("") == 0.0

    def test_score_chunk_calls_llm(self, mock_client):
        """_score_chunk sends a request and parses the returned content."""
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="0.6"))]
        )
        reranker = LLMReranker(client=mock_client, model="test-model")

        score = reranker._score_chunk("query", {"text": "some chunk"})

        assert score == 0.6
        mock_client.chat.completions.create.assert_called_once()
