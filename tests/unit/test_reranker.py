"""Tests for reranker.py (LLMReranker).

The LLM client is always mocked -- these are pure unit tests, no network.
The candidate chunks mirror the shape HybridRetriever.retrieve() produces
(id / text / blended ``score``) and reuse the same python/django/typescript
fixtures as test_hybrid.py so the two suites tell one coherent story.
"""

import json
from unittest.mock import Mock

import pytest

from rag.retriever.reranker import LLMReranker, RerankerConfig


def _fake_completion(content: str) -> Mock:
    """Build a stand-in for an OpenAI chat completion response object."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.content = content
    return response


def _client_returning(*contents: str) -> Mock:
    """A mock OpenAI client whose successive create() calls return the given
    payloads (as if the LLM replied with each in turn)."""
    client = Mock()
    client.chat.completions.create.side_effect = [_fake_completion(c) for c in contents]
    return client


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    @pytest.fixture
    def config(self) -> RerankerConfig:
        return RerankerConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
            batch_size=20,
        )

    @pytest.fixture
    def candidates(self) -> list[dict]:
        """Blend-sorted candidate pool: id 4 (unrelated) sits above id 3
        (django) exactly like the bug in test_hybrid.py."""
        return [
            {"id": 1, "text": "python programming language", "score": 0.90},
            {"id": 4, "text": "typescript rust golang", "score": 0.60},
            {"id": 3, "text": "python django framework", "score": 0.40},
        ]

    def test_rerank_reorders_by_llm_score(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """Chunks are reordered by the LLM's relevance scores, not the
        incoming blended order."""
        client = _client_returning(json.dumps({"1": 0.5, "4": 0.1, "3": 0.99}))
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python web development", candidates)

        assert [c["id"] for c in results] == [3, 1, 4]
        assert results[0]["llm_score"] == pytest.approx(0.99)

    def test_rerank_empty_pool_returns_empty_without_calling_llm(
        self, config: RerankerConfig
    ) -> None:
        """An empty candidate pool short-circuits -- no LLM call."""
        client = Mock()
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python", [])

        assert results == []
        client.chat.completions.create.assert_not_called()

    def test_rerank_llm_error_falls_back_to_original_order(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """If the LLM call raises, the original ordering is returned
        untouched and no llm_score is attached."""
        client = Mock()
        client.chat.completions.create.side_effect = RuntimeError("timeout")
        reranker = LLMReranker(config, client=client)

        original_ids = [c["id"] for c in candidates]
        results = reranker.rerank("python web development", candidates)

        assert [c["id"] for c in results] == original_ids
        assert all("llm_score" not in c for c in results)

    def test_rerank_malformed_output_falls_back(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """Unparseable (non-JSON) LLM output is treated as a no-op."""
        client = _client_returning("sorry, I cannot help with that")
        reranker = LLMReranker(config, client=client)

        original_ids = [c["id"] for c in candidates]
        results = reranker.rerank("python web development", candidates)

        assert [c["id"] for c in results] == original_ids
        assert all("llm_score" not in c for c in results)

    def test_rerank_partial_scores_keep_blended_score(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """When the LLM scores only some chunks, unscored ones fall back to
        their blended score for ordering (and gain no llm_score)."""
        # Only score id 3 (boost it high). ids 1 and 4 keep blended 0.90/0.60.
        client = _client_returning(json.dumps({"3": 0.95}))
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python web development", candidates)

        assert [c["id"] for c in results] == [3, 1, 4]
        by_id = {c["id"]: c for c in results}
        assert by_id[3]["llm_score"] == pytest.approx(0.95)
        assert "llm_score" not in by_id[1]
        assert "llm_score" not in by_id[4]

    def test_rerank_unknown_ids_are_ignored(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """Scores for ids that aren't in the pool are ignored, not crashed
        on; chunks with no valid score keep the blended order."""
        client = _client_returning(json.dumps({"999": 0.99, "nonexistent": 0.8}))
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python web development", candidates)

        assert [c["id"] for c in results] == [1, 4, 3]  # unchanged
        assert all("llm_score" not in c for c in results)

    def test_rerank_clamps_scores_to_unit_interval(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """Out-of-range LLM scores are clamped into [0.0, 1.0]."""
        client = _client_returning(json.dumps({"1": 1.5, "4": -0.3, "3": 0.5}))
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python web development", candidates)
        by_id = {c["id"]: c for c in results}

        assert by_id[1]["llm_score"] == pytest.approx(1.0)
        assert by_id[4]["llm_score"] == pytest.approx(0.0)
        assert by_id[3]["llm_score"] == pytest.approx(0.5)

    def test_rerank_ignores_non_numeric_scores(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """A non-numeric score for one id is skipped without failing the
        whole batch; other valid scores still apply."""
        client = _client_returning(json.dumps({"1": "high", "3": 0.99}))
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python web development", candidates)
        by_id = {c["id"]: c for c in results}

        assert results[0]["id"] == 3
        assert "llm_score" not in by_id[1]  # "high" ignored
        assert by_id[3]["llm_score"] == pytest.approx(0.99)

    def test_rerank_parses_json_in_code_fence(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """Scores wrapped in a ```json fence (a common LLM habit) still
        parse."""
        fenced = "Here you go:\n```json\n" + json.dumps({"3": 0.99}) + "\n```"
        client = _client_returning(fenced)
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("python web development", candidates)

        assert results[0]["id"] == 3
        assert results[0]["llm_score"] == pytest.approx(0.99)

    def test_rerank_batches_large_pool(self, config: RerankerConfig) -> None:
        """A pool larger than batch_size is split across multiple LLM calls
        rather than truncated."""
        config.batch_size = 2
        chunks = [{"id": i, "text": f"chunk {i}", "score": 1.0 - i * 0.1} for i in range(5)]
        # 5 chunks / batch_size 2 -> 3 batches -> 3 create() calls.
        client = _client_returning(
            json.dumps({"0": 0.1, "1": 0.2}),
            json.dumps({"2": 0.3, "3": 0.4}),
            json.dumps({"4": 0.9}),
        )
        reranker = LLMReranker(config, client=client)

        results = reranker.rerank("q", chunks)

        assert client.chat.completions.create.call_count == 3
        # id 4 got the top score across batches -> ranks first.
        assert results[0]["id"] == 4

    def test_rerank_does_not_mutate_ordering_of_input_list(
        self, config: RerankerConfig, candidates: list[dict]
    ) -> None:
        """rerank returns a new ordering; the caller's list order is left
        intact (only per-chunk llm_score annotations are added)."""
        client = _client_returning(json.dumps({"3": 0.99}))
        reranker = LLMReranker(config, client=client)

        reranker.rerank("python web development", candidates)

        # The original list object still holds its original order.
        assert [c["id"] for c in candidates] == [1, 4, 3]
