"""Tests for reranker.py"""

from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from rag.retriever.reranker import LLMReranker, RerankerConfig


def make_openai_response(content: str) -> Mock:
    """Build a minimal mock object shaped like an OpenAI chat completion response."""
    response = Mock()
    message = Mock()
    message.content = content
    choice = Mock()
    choice.message = message
    response.choices = [choice]
    return response


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    @pytest.fixture
    def config(self) -> RerankerConfig:
        """Create a RerankerConfig instance."""
        return RerankerConfig(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="test-model",
        )

    @pytest.fixture
    def reranker(self, config: RerankerConfig) -> Generator[LLMReranker, None, None]:
        """Create an LLMReranker instance with a patched OpenAI client."""
        with patch("rag.retriever.reranker.openai.OpenAI") as mock_openai_cls:
            mock_client = Mock()
            mock_openai_cls.return_value = mock_client
            instance = LLMReranker(config)
            instance.client = mock_client
            yield instance

    def test_empty_chunks_returns_empty(self, reranker: LLMReranker) -> None:
        """Test that an empty chunk list returns an empty list without calling the LLM."""
        result = reranker.rerank("some query", [], top_k=5)

        assert result == []
        reranker.client.chat.completions.create.assert_not_called()

    def test_rerank_orders_by_llm_score(self, reranker: LLMReranker) -> None:
        """Test that chunks are sorted by LLM-assigned relevance score."""
        chunks = [
            {"id": "a", "text": "irrelevant text", "score": 0.5},
            {"id": "b", "text": "very relevant text", "score": 0.4},
        ]

        reranker.client.chat.completions.create.side_effect = [
            make_openai_response("0.2"),
            make_openai_response("0.9"),
        ]

        result = reranker.rerank("query", chunks, top_k=2)

        assert [c["id"] for c in result] == ["b", "a"]
        assert result[0]["llm_score"] == 0.9
        assert result[1]["llm_score"] == 0.2

    def test_rerank_respects_top_k(self, reranker: LLMReranker) -> None:
        """Test that only top_k chunks are returned."""
        chunks = [
            {"id": "a", "text": "text a", "score": 0.5},
            {"id": "b", "text": "text b", "score": 0.5},
            {"id": "c", "text": "text c", "score": 0.5},
        ]

        reranker.client.chat.completions.create.side_effect = [
            make_openai_response("0.1"),
            make_openai_response("0.5"),
            make_openai_response("0.9"),
        ]

        result = reranker.rerank("query", chunks, top_k=2)

        assert len(result) == 2
        assert result[0]["id"] == "c"
        assert result[1]["id"] == "b"

    def test_original_chunk_fields_preserved(self, reranker: LLMReranker) -> None:
        """Test that rerank preserves original chunk fields alongside llm_score."""
        chunks = [
            {"id": "a", "text": "text", "score": 0.5, "metadata": {"source_id": "doc1"}},
        ]
        reranker.client.chat.completions.create.return_value = make_openai_response("0.7")

        result = reranker.rerank("query", chunks, top_k=1)

        assert result[0]["id"] == "a"
        assert result[0]["metadata"] == {"source_id": "doc1"}
        assert result[0]["score"] == 0.5
        assert result[0]["llm_score"] == 0.7

    def test_llm_call_failure_falls_back_to_blended_score(self, reranker: LLMReranker) -> None:
        """Test that an LLM call raising an exception falls back to the chunk's score."""
        chunks = [{"id": "a", "text": "text", "score": 0.42}]
        reranker.client.chat.completions.create.side_effect = RuntimeError("API down")

        result = reranker.rerank("query", chunks, top_k=1)

        assert result[0]["llm_score"] == 0.42

    def test_unparseable_llm_output_falls_back_to_blended_score(
        self, reranker: LLMReranker
    ) -> None:
        """Test that non-numeric LLM output falls back to the chunk's score."""
        chunks = [{"id": "a", "text": "text", "score": 0.33}]
        reranker.client.chat.completions.create.return_value = make_openai_response("not a number")

        result = reranker.rerank("query", chunks, top_k=1)

        assert result[0]["llm_score"] == 0.33

    def test_out_of_range_llm_score_falls_back(self, reranker: LLMReranker) -> None:
        """Test that an out-of-range LLM score falls back to the chunk's score."""
        chunks = [{"id": "a", "text": "text", "score": 0.6}]
        reranker.client.chat.completions.create.return_value = make_openai_response("5.0")

        result = reranker.rerank("query", chunks, top_k=1)

        assert result[0]["llm_score"] == 0.6

    def test_missing_score_key_falls_back_to_zero(self, reranker: LLMReranker) -> None:
        """Test that a chunk missing the 'score' key falls back to 0.0 on failure."""
        chunks = [{"id": "a", "text": "text"}]
        reranker.client.chat.completions.create.side_effect = RuntimeError("API down")

        result = reranker.rerank("query", chunks, top_k=1)

        assert result[0]["llm_score"] == 0.0

    def test_llm_called_once_per_chunk(self, reranker: LLMReranker) -> None:
        """Test that the LLM is called exactly once per input chunk."""
        chunks = [
            {"id": "a", "text": "text a", "score": 0.5},
            {"id": "b", "text": "text b", "score": 0.5},
            {"id": "c", "text": "text c", "score": 0.5},
        ]
        reranker.client.chat.completions.create.return_value = make_openai_response("0.5")

        reranker.rerank("query", chunks, top_k=3)

        assert reranker.client.chat.completions.create.call_count == 3

    def test_prompt_includes_query_and_chunk_text(self, reranker: LLMReranker) -> None:
        """Test that the prompt sent to the LLM includes the query and chunk text."""
        chunks = [{"id": "a", "text": "unique chunk content", "score": 0.5}]
        reranker.client.chat.completions.create.return_value = make_openai_response("0.5")

        reranker.rerank("unique query text", chunks, top_k=1)

        call_kwargs = reranker.client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        user_message = messages[-1]["content"]
        assert "unique query text" in user_message
        assert "unique chunk content" in user_message
