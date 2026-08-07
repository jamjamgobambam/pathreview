"""Tests for reranker.py and the HybridRetriever re-rank toggle (issue #34)."""

import json
from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.reranker import LLMReranker, RerankConfig


def _make_reranker() -> LLMReranker:
    """Build an LLMReranker whose OpenAI client will be replaced with a Mock."""
    config = RerankConfig(api_key="test", base_url="http://test", model="test-model")
    return LLMReranker(config)


def _mock_llm_response(payload) -> Mock:
    """Wrap a payload (JSON-serializable object or raw string) in the OpenAI
    chat-completion response shape."""
    message = Mock()
    message.content = payload if isinstance(payload, str) else json.dumps(payload)
    choice = Mock()
    choice.message = message
    response = Mock()
    response.choices = [choice]
    return response


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    def test_rerank_reorders_by_llm_score(self):
        """A low-blend chunk the LLM judges most relevant is promoted to the top."""
        reranker = _make_reranker()
        # Input order is the blended order: a (best blend) then b then c.
        chunks = [
            {"id": "a", "text": "a", "score": 0.9},
            {"id": "b", "text": "b", "score": 0.5},
            {"id": "c", "text": "c", "score": 0.4},
        ]
        # But the LLM finds c most relevant, a least.
        reranker.client = Mock()
        reranker.client.chat.completions.create.return_value = _mock_llm_response(
            [
                {"index": 0, "score": 0.1},
                {"index": 1, "score": 0.5},
                {"index": 2, "score": 0.9},
            ]
        )

        results = reranker.rerank("query", chunks, top_k=3)

        assert [c["id"] for c in results] == ["c", "b", "a"]
        assert results[0]["rerank_score"] == 0.9

    def test_rerank_empty_returns_empty(self):
        """Empty candidate set returns [] without calling the LLM."""
        reranker = _make_reranker()
        reranker.client = Mock()

        assert reranker.rerank("query", [], top_k=5) == []
        reranker.client.chat.completions.create.assert_not_called()

    def test_rerank_falls_back_to_blended_order_on_error(self):
        """If the LLM call raises, original blended order is preserved."""
        reranker = _make_reranker()
        chunks = [
            {"id": "a", "text": "a", "score": 0.9},
            {"id": "b", "text": "b", "score": 0.5},
        ]
        reranker.client = Mock()
        reranker.client.chat.completions.create.side_effect = RuntimeError("boom")

        results = reranker.rerank("query", chunks, top_k=2)

        assert [c["id"] for c in results] == ["a", "b"]

    def test_rerank_partial_response_falls_back_to_blended(self):
        """A response missing a score for any chunk falls back to blended order,
        so a highly-blended chunk is never buried by an omitted index."""
        reranker = _make_reranker()
        chunks = [
            {"id": "a", "text": "a", "score": 0.9},
            {"id": "b", "text": "b", "score": 0.5},
            {"id": "c", "text": "c", "score": 0.4},
        ]
        # LLM scores only two of the three chunks.
        reranker.client = Mock()
        reranker.client.chat.completions.create.return_value = _mock_llm_response(
            [{"index": 0, "score": 0.1}, {"index": 1, "score": 0.2}]
        )

        results = reranker.rerank("query", chunks, top_k=3)

        assert [c["id"] for c in results] == ["a", "b", "c"]

    def test_rerank_does_not_mutate_input_chunks(self):
        """rerank() must not add rerank_score to the caller's original dicts."""
        reranker = _make_reranker()
        chunks = [{"id": "a", "text": "a", "score": 0.9}]
        reranker.client = Mock()
        reranker.client.chat.completions.create.return_value = _mock_llm_response(
            [{"index": 0, "score": 0.7}]
        )

        reranker.rerank("query", chunks, top_k=1)

        assert "rerank_score" not in chunks[0]

    def test_parse_scores_skips_malformed_entries(self):
        """Malformed entries are dropped; well-formed ones are clamped to 0-1."""
        content = json.dumps(
            [
                {"index": 0, "score": 0.8},
                {"index": 1},  # missing score -> skipped
                {"index": 2, "score": 1.5},  # clamped to 1.0
            ]
        )

        scores = LLMReranker._parse_scores(content)

        assert scores == {0: 0.8, 2: 1.0}

    def test_parse_scores_strips_code_fences(self):
        """JSON wrapped in a Markdown code fence is parsed, not discarded."""
        content = '```json\n[{"index": 0, "score": 0.6}]\n```'

        scores = LLMReranker._parse_scores(content)

        assert scores == {0: 0.6}


@pytest.mark.unit
class TestHybridRerankToggle:
    """The enable_rerank toggle on HybridRetriever."""

    def _retriever(self, reranker=None, enable_rerank=False):
        vector_store = Mock()
        vector_store.query.return_value = [
            {"id": "a", "score": 0.9, "text": "a", "metadata": {}},
            {"id": "b", "score": 0.5, "text": "b", "metadata": {}},
        ]
        keyword_searcher = Mock()
        keyword_searcher.search.return_value = []
        return HybridRetriever(
            vector_store,
            keyword_searcher,
            reranker=reranker,
            enable_rerank=enable_rerank,
        )

    def test_disabled_toggle_keeps_blended_order(self):
        """With rerank off, retrieve() returns the blended-score order (no-op)."""
        reranker = Mock()
        retriever = self._retriever(reranker=reranker, enable_rerank=False)

        results = retriever.retrieve("q", "p", [0.1, 0.2], max_chunks=2, min_score=0.0)

        reranker.rerank.assert_not_called()
        assert [r["id"] for r in results] == ["a", "b"]

    def test_enabled_toggle_delegates_to_reranker(self):
        """With rerank on, retrieve() hands the candidate set to the reranker."""
        reranker = Mock()
        reranker.rerank.return_value = [{"id": "b"}, {"id": "a"}]
        retriever = self._retriever(reranker=reranker, enable_rerank=True)

        results = retriever.retrieve("q", "p", [0.1, 0.2], max_chunks=2, min_score=0.0)

        reranker.rerank.assert_called_once()
        assert [r["id"] for r in results] == ["b", "a"]
