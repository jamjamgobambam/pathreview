"""Tests for LLMReranker — issue #34."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    def test_reranker_module_exists(self) -> None:
        """LLMReranker class should exist in rag.retriever.reranker."""
        from rag.retriever.reranker import LLMReranker  # noqa: F401

    def test_reranker_rerank_returns_list(self) -> None:
        """rerank() should return a list of chunks."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="[0.9, 0.8]"))]
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
            choices=[MagicMock(message=MagicMock(content="[0.85]"))]
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

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="[0.3, 0.9, 0.6]"))]
        )

        reranker = LLMReranker(client=mock_client, model="mock-model")
        chunks = [
            {"id": "a", "text": "low relevance", "score": 0.9},
            {"id": "b", "text": "high relevance", "score": 0.5},
            {"id": "c", "text": "medium relevance", "score": 0.7},
        ]

        result = reranker.rerank(query="query", chunks=chunks)

        rerank_scores = [r["rerank_score"] for r in result]
        assert rerank_scores == sorted(rerank_scores, reverse=True)

    def test_reranker_makes_single_api_call(self) -> None:
        """rerank() should score all chunks in one API call, not one per chunk."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="[0.9, 0.5, 0.7]"))]
        )

        reranker = LLMReranker(client=mock_client, model="mock-model")
        chunks = [
            {"id": "a", "text": "chunk a", "score": 0.8},
            {"id": "b", "text": "chunk b", "score": 0.6},
            {"id": "c", "text": "chunk c", "score": 0.4},
        ]

        reranker.rerank(query="query", chunks=chunks)

        mock_client.chat.completions.create.assert_called_once()

    def test_reranker_uses_temperature_zero(self) -> None:
        """rerank() should call the LLM with temperature=0 for deterministic scoring."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="[0.8]"))]
        )

        reranker = LLMReranker(client=mock_client, model="mock-model")
        reranker.rerank(query="query", chunks=[{"id": "a", "text": "text", "score": 0.5}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("temperature") == 0

    def test_reranker_llm_failure_falls_back_to_original_scores(self) -> None:
        """rerank() should fall back to original scores when the LLM call fails."""
        from rag.retriever.reranker import LLMReranker

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("network error")

        reranker = LLMReranker(client=mock_client, model="mock-model")
        chunks = [
            {"id": "a", "text": "chunk a", "score": 0.8},
            {"id": "b", "text": "chunk b", "score": 0.6},
        ]

        result = reranker.rerank(query="query", chunks=chunks)

        assert len(result) == 2
        assert all("rerank_score" in r for r in result)
        scores = {r["id"]: r["rerank_score"] for r in result}
        assert scores["a"] == 0.8
        assert scores["b"] == 0.6

    def test_hybrid_retriever_accepts_optional_reranker(self) -> None:
        """HybridRetriever.__init__ should accept an optional reranker parameter."""
        import inspect

        from rag.retriever.hybrid import HybridRetriever

        sig = inspect.signature(HybridRetriever.__init__)
        assert "reranker" in sig.parameters


@pytest.mark.unit
class TestParseScores:
    """Tests for LLMReranker._parse_scores."""

    def test_valid_json_array_parsed(self) -> None:
        """A clean JSON array is parsed into floats."""
        from rag.retriever.reranker import LLMReranker

        result = LLMReranker._parse_scores("[0.8, 0.3, 0.95]", fallbacks=[0.5, 0.5, 0.5])
        assert result == [0.8, 0.3, 0.95]

    def test_value_above_one_uses_fallback(self) -> None:
        """A score above 1.0 (e.g. model rated 8/10) should use the fallback."""
        from rag.retriever.reranker import LLMReranker

        result = LLMReranker._parse_scores("[8.0]", fallbacks=[0.5])
        assert result == [0.5]

    def test_preamble_number_does_not_steal_score(self) -> None:
        """A number in a preamble like 'Chunk 3 scores 0.4' should not become the score."""
        from rag.retriever.reranker import LLMReranker

        result = LLMReranker._parse_scores("[0.4]", fallbacks=[0.5])
        assert result == [0.4]

    def test_non_json_response_uses_fallbacks(self) -> None:
        """A response with no JSON array falls back to original scores."""
        from rag.retriever.reranker import LLMReranker

        result = LLMReranker._parse_scores("I cannot score this.", fallbacks=[0.6, 0.4])
        assert result == [0.6, 0.4]

    def test_wrong_count_uses_fallbacks(self) -> None:
        """A JSON array with the wrong number of scores falls back entirely."""
        from rag.retriever.reranker import LLMReranker

        result = LLMReranker._parse_scores("[0.8, 0.3]", fallbacks=[0.5, 0.5, 0.5])
        assert result == [0.5, 0.5, 0.5]

    def test_json_array_embedded_in_text(self) -> None:
        """A JSON array embedded in surrounding text is still parsed correctly."""
        from rag.retriever.reranker import LLMReranker

        result = LLMReranker._parse_scores("Here are the scores: [0.7, 0.2]", fallbacks=[0.5, 0.5])
        assert result == [0.7, 0.2]


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
