"""Tests for LLMReranker — issue #34."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for the not-yet-implemented LLMReranker."""

    def test_reranker_module_exists(self) -> None:
        """LLMReranker class should exist in rag.retriever.reranker."""
        from rag.retriever.reranker import LLMReranker  # noqa: F401

    def test_reranker_rerank_returns_list(self) -> None:
        """rerank() should return a list of chunks."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="0.9"))]
        )

        reranker = LLMReranker(client=mock_client, model="mock-model")
        chunks = [
            {"id": "a", "text": "somewhat relevant content", "score": 0.8},
            {"id": "b", "text": "very relevant python skills", "score": 0.7},
        ]

        result = reranker.rerank(query="python skills", chunks=chunks)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_reranker_adds_rerank_score(self) -> None:
        """Each chunk returned by rerank() should have a rerank_score field."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="0.85"))]
        )

        reranker = LLMReranker(client=mock_client, model="mock-model")
        chunks = [{"id": "a", "text": "python skills section", "score": 0.8}]

        result = reranker.rerank(query="python", chunks=chunks)

        assert "rerank_score" in result[0]
        assert isinstance(result[0]["rerank_score"], float)

    def test_reranker_empty_chunks_returns_empty(self) -> None:
        """rerank() with empty input should return empty list without calling LLM."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        reranker = LLMReranker(client=mock_client, model="mock-model")

        result = reranker.rerank(query="python", chunks=[])

        assert result == []
        mock_client.chat.completions.create.assert_not_called()

    def test_reranker_sorts_by_rerank_score_descending(self) -> None:
        """rerank() should return chunks sorted by rerank_score, highest first."""
        from rag.retriever.reranker import LLMReranker

        scores = ["0.3", "0.9", "0.6"]
        call_count = 0

        def fake_create(**kwargs: object) -> MagicMock:
            nonlocal call_count
            score = scores[call_count % len(scores)]
            call_count += 1
            return MagicMock(choices=[MagicMock(message=MagicMock(content=score))])

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = fake_create

        reranker = LLMReranker(client=mock_client, model="mock-model")
        chunks = [
            {"id": "a", "text": "low relevance", "score": 0.9},
            {"id": "b", "text": "high relevance", "score": 0.5},
            {"id": "c", "text": "medium relevance", "score": 0.7},
        ]

        result = reranker.rerank(query="query", chunks=chunks)

        rerank_scores = [r["rerank_score"] for r in result]
        assert rerank_scores == sorted(rerank_scores, reverse=True)

    def test_hybrid_retriever_accepts_optional_reranker(self) -> None:
        """HybridRetriever.__init__ should accept an optional reranker parameter."""
        import inspect

        from rag.retriever.hybrid import HybridRetriever

        sig = inspect.signature(HybridRetriever.__init__)
        assert "reranker" in sig.parameters


@pytest.mark.unit
class TestBuildReranker:
    """Tests for the build_reranker() factory."""

    def test_build_reranker_returns_none_when_no_api_key(self) -> None:
        """build_reranker() should return None when GROQ_API_KEY is not set."""
        from rag.retriever.reranker import build_reranker

        mock_settings = MagicMock()
        mock_settings.groq_api_key = ""

        with patch("rag.retriever.reranker.settings", mock_settings):
            result = build_reranker()

        assert result is None

    def test_build_reranker_returns_llm_reranker_when_key_set(self) -> None:
        """build_reranker() should return an LLMReranker when GROQ_API_KEY is set."""
        from rag.retriever.reranker import LLMReranker, build_reranker

        mock_settings = MagicMock()
        mock_settings.groq_api_key = "gsk_test_key"
        mock_settings.groq_base_url = "https://api.groq.com/openai/v1"
        mock_settings.groq_model = "llama-3.3-70b-versatile"

        with (
            patch("rag.retriever.reranker.settings", mock_settings),
            patch("rag.retriever.reranker.openai.OpenAI") as mock_openai,
        ):
            result = build_reranker()

        assert isinstance(result, LLMReranker)
        mock_openai.assert_called_once_with(
            api_key="gsk_test_key",
            base_url="https://api.groq.com/openai/v1",
        )

    def test_build_reranker_uses_groq_model(self) -> None:
        """build_reranker() should configure LLMReranker with the groq_model."""
        from rag.retriever.reranker import build_reranker

        mock_settings = MagicMock()
        mock_settings.groq_api_key = "gsk_test_key"
        mock_settings.groq_base_url = "https://api.groq.com/openai/v1"
        mock_settings.groq_model = "llama-3.3-70b-versatile"

        with (
            patch("rag.retriever.reranker.settings", mock_settings),
            patch("rag.retriever.reranker.openai.OpenAI"),
        ):
            result = build_reranker()

        assert result is not None
        assert result.model == "llama-3.3-70b-versatile"
