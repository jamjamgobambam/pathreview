"""Tests for reranker.py"""

import json
from unittest.mock import Mock, patch

import pytest

from rag.retriever.reranker import Reranker, RerankerConfig


def _make_response(content: str) -> Mock:
    """Build a fake OpenAI chat-completions response with the given content."""
    response = Mock()
    response.choices = [Mock(message=Mock(content=content))]
    return response


@pytest.mark.unit
class TestReranker:
    """Test suite for Reranker."""

    @pytest.fixture
    def config(self) -> RerankerConfig:
        return RerankerConfig(
            api_key="test-key", base_url="https://example.invalid/v1", model="test-model"
        )

    @pytest.fixture
    def reranker(self, config: RerankerConfig) -> Reranker:
        with patch("rag.retriever.reranker.openai.OpenAI"):
            return Reranker(config)

    @pytest.fixture
    def chunks(self) -> list[dict]:
        """The same keyword-stuffing-vs-relevance scenario from test_hybrid_keyword_bias.py."""
        return [
            {"id": "stuffed", "text": "kubernetes " * 6 + "pizza toppings recipe", "score": 0.883},
            {
                "id": "relevant",
                "text": "our team migrated the payment service to a managed kubernetes cluster",
                "score": 0.851,
            },
        ]

    def test_empty_chunks_returns_empty(self, reranker: Reranker) -> None:
        """No chunks in -> no LLM call, empty list out."""
        assert reranker.rerank("kubernetes deployment", []) == []

    def test_reranker_corrects_keyword_stuffing_bias(
        self, reranker: Reranker, chunks: list[dict]
    ) -> None:
        """Confirms the reranker can invert the ordering test_hybrid_keyword_bias.py showcased.

        HybridRetriever's blended score ranked "stuffed" (0.883) above "relevant"
        (0.851) purely due to keyword repetition. Here the (mocked) LLM correctly
        judges "relevant" as more topically relevant, and the reranker output
        should reflect that corrected order.
        """
        reranker.client.chat.completions.create.return_value = _make_response(
            json.dumps({"relevant": 0.95, "stuffed": 0.1})
        )

        results = reranker.rerank("kubernetes deployment", chunks)

        assert [r["id"] for r in results] == ["relevant", "stuffed"]
        assert results[0]["rerank_score"] == 0.95
        assert results[1]["rerank_score"] == 0.1

    def test_top_k_truncates_results(self, reranker: Reranker, chunks: list[dict]) -> None:
        reranker.client.chat.completions.create.return_value = _make_response(
            json.dumps({"relevant": 0.95, "stuffed": 0.1})
        )

        results = reranker.rerank("kubernetes deployment", chunks, top_k=1)

        assert len(results) == 1
        assert results[0]["id"] == "relevant"

    def test_llm_call_failure_falls_back_to_blended_score_order(
        self, reranker: Reranker, chunks: list[dict]
    ) -> None:
        """If the LLM call errors, fall back to the original blended-score order
        rather than breaking retrieval -- this still exhibits the keyword-bias
        problem, but degrades safely instead of raising."""
        reranker.client.chat.completions.create.side_effect = RuntimeError("API unavailable")

        results = reranker.rerank("kubernetes deployment", chunks)

        assert [r["id"] for r in results] == ["stuffed", "relevant"]
        assert "rerank_score" not in results[0]

    def test_malformed_llm_output_falls_back_to_blended_score_order(
        self, reranker: Reranker, chunks: list[dict]
    ) -> None:
        """If the LLM doesn't return parseable JSON, fall back gracefully."""
        reranker.client.chat.completions.create.return_value = _make_response(
            "sorry, I cannot help with that"
        )

        results = reranker.rerank("kubernetes deployment", chunks)

        assert [r["id"] for r in results] == ["stuffed", "relevant"]

    def test_missing_chunk_id_in_response_falls_back_to_its_blended_score(
        self, reranker: Reranker, chunks: list[dict]
    ) -> None:
        """If the LLM only scores some chunks, the unscored ones keep their
        original blended score rather than being dropped or scored 0."""
        reranker.client.chat.completions.create.return_value = _make_response(
            json.dumps({"relevant": 0.95})
        )

        results = reranker.rerank("kubernetes deployment", chunks)

        by_id = {r["id"]: r for r in results}
        assert by_id["stuffed"]["rerank_score"] == 0.883  # fell back to its own "score"
        assert by_id["relevant"]["rerank_score"] == 0.95
        assert [r["id"] for r in results] == ["relevant", "stuffed"]
