"""Tests for reranker.py"""

from unittest.mock import Mock, patch

import pytest

from rag.retriever.reranker import (
    LLMReranker,
    MockReranker,
    Reranker,
    get_reranker,
)


@pytest.mark.unit
class TestMockReranker:
    """Test suite for MockReranker."""

    @pytest.fixture
    def reranker(self):
        return MockReranker()

    def test_results_sorted_by_rerank_score_descending(self, reranker):
        chunks = [
            {"id": 1, "text": "java development platform"},
            {"id": 2, "text": "python programming language"},
            {"id": 3, "text": "python django framework tutorial"},
        ]

        results = reranker.rerank("python framework", chunks)

        scores = [r["rerank_score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert results[0]["id"] == 3

    def test_preserves_original_fields(self, reranker):
        chunks = [{"id": 1, "text": "python", "metadata": {"source_id": "abc"}}]

        results = reranker.rerank("python", chunks)

        assert results[0]["id"] == 1
        assert results[0]["metadata"] == {"source_id": "abc"}
        assert "rerank_score" in results[0]

    def test_empty_chunks_returns_empty(self, reranker):
        assert reranker.rerank("python", []) == []

    def test_empty_query_scores_zero(self, reranker):
        chunks = [{"id": 1, "text": "python programming"}]
        results = reranker.rerank("", chunks)

        assert results[0]["rerank_score"] == 0.0

    def test_deterministic(self, reranker):
        chunks = [{"id": 1, "text": "python programming"}]

        first = reranker.rerank("python", chunks)
        second = reranker.rerank("python", chunks)

        assert first[0]["rerank_score"] == second[0]["rerank_score"]

    def test_is_reranker_subclass(self, reranker):
        assert isinstance(reranker, Reranker)


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    def _make_reranker_with_response(self, content: str) -> LLMReranker:
        with patch("rag.retriever.reranker.openai.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=content))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            reranker = LLMReranker(api_key="key", base_url="http://example.com", model="mock-model")
            reranker.client = mock_client
            return reranker

    def test_parses_numeric_score_from_response(self):
        reranker = self._make_reranker_with_response("0.85")

        results = reranker.rerank("query", [{"id": 1, "text": "some text"}])

        assert results[0]["rerank_score"] == pytest.approx(0.85)

    def test_clamps_score_above_one(self):
        reranker = self._make_reranker_with_response("3.5")

        results = reranker.rerank("query", [{"id": 1, "text": "some text"}])

        assert results[0]["rerank_score"] == 1.0

    def test_clamps_score_below_zero(self):
        reranker = self._make_reranker_with_response("-2")

        results = reranker.rerank("query", [{"id": 1, "text": "some text"}])

        assert results[0]["rerank_score"] == 0.0

    def test_unparseable_response_scores_zero(self):
        reranker = self._make_reranker_with_response("not a number")

        results = reranker.rerank("query", [{"id": 1, "text": "some text"}])

        assert results[0]["rerank_score"] == 0.0

    def test_llm_error_falls_back_to_zero(self):
        with patch("rag.retriever.reranker.openai.OpenAI"):
            reranker = LLMReranker(api_key="key", base_url="http://example.com", model="mock-model")
            reranker.client = Mock()
            reranker.client.chat.completions.create.side_effect = Exception("boom")

            results = reranker.rerank("query", [{"id": 1, "text": "some text"}])

        assert results[0]["rerank_score"] == 0.0

    def test_results_sorted_by_score_descending(self):
        with patch("rag.retriever.reranker.openai.OpenAI"):
            reranker = LLMReranker(api_key="key", base_url="http://example.com", model="mock-model")
            reranker.client = Mock()

            responses = ["0.2", "0.9", "0.5"]
            reranker.client.chat.completions.create.side_effect = [
                Mock(choices=[Mock(message=Mock(content=r))]) for r in responses
            ]

            chunks = [{"id": 1, "text": "a"}, {"id": 2, "text": "b"}, {"id": 3, "text": "c"}]
            results = reranker.rerank("query", chunks)

        assert [r["id"] for r in results] == [2, 3, 1]

    def test_is_reranker_subclass(self):
        with patch("rag.retriever.reranker.openai.OpenAI"):
            reranker = LLMReranker(api_key="key", base_url="http://example.com", model="mock-model")

        assert isinstance(reranker, Reranker)


@pytest.mark.unit
class TestGetReranker:
    """Test suite for the get_reranker factory."""

    def test_mock_provider(self):
        reranker = get_reranker("mock")
        assert isinstance(reranker, MockReranker)

    def test_mock_provider_case_insensitive(self):
        reranker = get_reranker("MOCK")
        assert isinstance(reranker, MockReranker)

    def test_llm_provider(self):
        with patch("rag.retriever.reranker.openai.OpenAI"):
            reranker = get_reranker("llm", api_key="key", base_url="http://example.com", model="m")

        assert isinstance(reranker, LLMReranker)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            get_reranker("bogus")
