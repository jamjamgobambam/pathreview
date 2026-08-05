"""Tests for reranker.py (issue #34: LLM chunk re-ranking)."""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.reranker import LLMReranker, RerankConfig


def _response(content: str | None) -> Mock:
    """Build a fake OpenAI chat completion response with the given content."""
    message = Mock()
    message.content = content
    choice = Mock()
    choice.message = message
    response = Mock()
    response.choices = [choice]
    return response


@pytest.mark.unit
class TestLLMReranker:
    """Test suite for LLMReranker."""

    @pytest.fixture
    def config(self) -> RerankConfig:
        """Create a RerankConfig with dummy credentials."""
        return RerankConfig(
            api_key="test-key",
            base_url="http://test.local",
            model="test-model",
        )

    @pytest.fixture
    def reranker(self, config: RerankConfig) -> LLMReranker:
        """Create an LLMReranker whose client is replaced with a Mock."""
        rr = LLMReranker(config)
        rr.client = Mock()
        return rr

    def _set_scores(self, reranker: LLMReranker, contents: list[str | None]) -> None:
        """Queue the LLM string responses returned per chunk, in order."""
        reranker.client.chat.completions.create.side_effect = [_response(c) for c in contents]

    def test_empty_chunks_returns_empty(self, reranker: LLMReranker) -> None:
        """Empty chunk list returns empty and never calls the LLM."""
        result = reranker.rerank("query", [])

        assert result == []
        reranker.client.chat.completions.create.assert_not_called()

    def test_empty_query_returns_empty(self, reranker: LLMReranker) -> None:
        """Empty query returns empty and never calls the LLM."""
        result = reranker.rerank("", [{"id": 1, "text": "content"}])

        assert result == []
        reranker.client.chat.completions.create.assert_not_called()

    def test_reorders_chunks_by_llm_score(self, reranker: LLMReranker) -> None:
        """A low-hybrid-score but relevant chunk is promoted to the top."""
        chunks = [
            {"id": 1, "text": "java spring boot", "score": 0.9},
            {"id": 2, "text": "python django web framework", "score": 0.4},
        ]
        # LLM scores chunk 1 low (2/10) and chunk 2 high (9/10).
        self._set_scores(reranker, ["2", "9"])

        result = reranker.rerank("python web framework", chunks)

        assert [c["id"] for c in result] == [2, 1]
        assert result[0]["rerank_score"] == pytest.approx(0.9)
        assert result[1]["rerank_score"] == pytest.approx(0.2)

    def test_rerank_score_added_and_normalized(self, reranker: LLMReranker) -> None:
        """Every returned chunk gains a rerank_score in [0.0, 1.0]."""
        chunks = [{"id": 1, "text": "a"}, {"id": 2, "text": "b"}]
        self._set_scores(reranker, ["7", "3"])

        result = reranker.rerank("q", chunks)

        for chunk in result:
            assert "rerank_score" in chunk
            assert 0.0 <= chunk["rerank_score"] <= 1.0

    def test_top_k_truncates_results(self, reranker: LLMReranker) -> None:
        """top_k limits the number of returned chunks."""
        chunks = [{"id": i, "text": f"chunk {i}"} for i in range(5)]
        self._set_scores(reranker, ["1", "2", "3", "4", "5"])

        result = reranker.rerank("q", chunks, top_k=2)

        assert len(result) == 2
        # Highest scored (id=4 -> "5", id=3 -> "4") come first.
        assert [c["id"] for c in result] == [4, 3]

    def test_original_chunk_fields_preserved(self, reranker: LLMReranker) -> None:
        """Re-ranking preserves original chunk fields."""
        chunks = [{"id": 1, "text": "hello", "metadata": {"source": "readme"}}]
        self._set_scores(reranker, ["8"])

        result = reranker.rerank("q", chunks)

        assert result[0]["id"] == 1
        assert result[0]["text"] == "hello"
        assert result[0]["metadata"] == {"source": "readme"}

    def test_llm_failure_falls_back_to_hybrid_score(self, reranker: LLMReranker) -> None:
        """An LLM/API exception falls back to the chunk's existing score."""
        chunks = [
            {"id": 1, "text": "a", "score": 0.8},
            {"id": 2, "text": "b", "score": 0.2},
        ]
        reranker.client.chat.completions.create.side_effect = RuntimeError("rate limit")

        result = reranker.rerank("q", chunks)

        # Falls back to hybrid ordering (0.8 > 0.2), scores mirror hybrid score.
        assert [c["id"] for c in result] == [1, 2]
        assert result[0]["rerank_score"] == pytest.approx(0.8)
        assert result[1]["rerank_score"] == pytest.approx(0.2)

    def test_unparseable_output_falls_back(self, reranker: LLMReranker) -> None:
        """Non-numeric LLM output falls back to the existing score."""
        chunks = [{"id": 1, "text": "a", "score": 0.55}]
        self._set_scores(reranker, ["no score available"])

        result = reranker.rerank("q", chunks)

        assert result[0]["rerank_score"] == pytest.approx(0.55)

    def test_chunk_without_text_skips_llm(self, reranker: LLMReranker) -> None:
        """A chunk with no text uses its fallback score without calling the LLM."""
        chunks = [{"id": 1, "score": 0.42}]

        result = reranker.rerank("q", chunks)

        assert result[0]["rerank_score"] == pytest.approx(0.42)
        reranker.client.chat.completions.create.assert_not_called()

    def test_score_extracted_from_verbose_output(self, reranker: LLMReranker) -> None:
        """A score embedded in prose is still parsed (first number wins)."""
        chunks = [{"id": 1, "text": "a"}]
        self._set_scores(reranker, ["Score: 8 out of 10"])

        result = reranker.rerank("q", chunks)

        assert result[0]["rerank_score"] == pytest.approx(0.8)

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("0", 0.0),
            ("10", 1.0),
            ("5", 0.5),
            ("7.5", 0.75),
            ("15", 1.0),  # clamped down to 10
            ("-3", 0.0),  # clamped up to 0
        ],
    )
    def test_parse_score_normalizes_and_clamps(self, raw: str, expected: float) -> None:
        """_parse_score normalizes 0-10 to 0-1 and clamps out-of-range values."""
        assert LLMReranker._parse_score(raw) == pytest.approx(expected)

    @pytest.mark.parametrize("raw", [None, "", "not a number"])
    def test_parse_score_returns_none_without_number(self, raw: str | None) -> None:
        """_parse_score returns None when no number is present."""
        assert LLMReranker._parse_score(raw) is None


@pytest.mark.unit
class TestHybridRerankerIntegration:
    """Verify HybridRetriever wires the reranker into retrieve()."""

    def _build_retriever(self, reranker: object | None) -> HybridRetriever:
        """Build a HybridRetriever with mocked stores and the given reranker."""
        vector_store = Mock()
        vector_store.query.return_value = [
            {"id": "a", "score": 0.4, "text": "python django", "metadata": {}},
            {"id": "b", "score": 0.9, "text": "java spring", "metadata": {}},
        ]

        keyword_searcher = Mock()
        keyword_searcher.search.return_value = []

        return HybridRetriever(
            vector_store, keyword_searcher, reranker=reranker  # type: ignore[arg-type]
        )

    def test_retrieve_uses_reranker_when_provided(self) -> None:
        """When a reranker is set, retrieve() delegates ordering to it."""
        reranker = Mock()
        # Reranker flips ordering: promote "a" above "b".
        reranker.rerank.side_effect = lambda query, chunks: sorted(
            chunks, key=lambda c: 0 if c["id"] == "a" else 1
        )
        retriever = self._build_retriever(reranker)

        results = retriever.retrieve("python web", "p1", [0.1, 0.2], max_chunks=5, min_score=0.0)

        reranker.rerank.assert_called_once()
        assert [r["id"] for r in results] == ["a", "b"]

    def test_retrieve_without_reranker_unchanged(self) -> None:
        """Without a reranker, retrieve() keeps pure hybrid ordering."""
        retriever = self._build_retriever(None)

        results = retriever.retrieve("python web", "p1", [0.1, 0.2], max_chunks=5, min_score=0.0)

        # Pure hybrid ordering sorts by blended score descending ("b" > "a").
        assert [r["id"] for r in results] == ["b", "a"]
