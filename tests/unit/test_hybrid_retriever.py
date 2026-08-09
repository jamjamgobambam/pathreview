"""Tests for hybrid.py — HybridRetriever score blending (regression for issue #24)."""

import pytest

from rag.retriever.hybrid import HybridRetriever


class FakeVectorStore:
    """Minimal VectorStore stand-in returning canned query results."""

    def __init__(self, results):
        self._results = results

    def query(self, query_embedding, collection_name, n_results=10):
        return self._results

    def get_collection(self, name):
        class _Empty:
            def get(self, include=None):
                return {"ids": [], "documents": [], "metadatas": []}

        return _Empty()


class FakeKeywordSearcher:
    """Minimal KeywordSearcher stand-in returning canned search results."""

    def __init__(self, results):
        self._results = results

    def search(self, query, top_k=10):
        return self._results


@pytest.mark.unit
class TestHybridRetrieverBlend:
    """Regression tests for the vector/keyword score blend (issue #24)."""

    # Scenario for query "React":
    #   resume-1 (CORRECT doc) — strong semantic match, weak keyword match
    #   readme-1 (WRONG doc)   — weak semantic match, keyword-stuffed
    @pytest.fixture
    def vector_results(self):
        return [
            {
                "id": "resume-1",
                "text": "Built a dashboard in React for a client",
                "metadata": {"source_id": "resume"},
                "score": 0.85,
            },
            {
                "id": "readme-1",
                "text": "React React React npm install react react-dom",
                "metadata": {"source_id": "readme"},
                "score": 0.50,
            },
        ]

    @pytest.fixture
    def keyword_results(self):
        return [
            {
                "id": "readme-1",
                "text": "React React React npm install react react-dom",
                "metadata": {"source_id": "readme"},
                "bm25_score": 9.0,
            },
            {
                "id": "resume-1",
                "text": "Built a dashboard in React for a client",
                "metadata": {"source_id": "resume"},
                "bm25_score": 3.0,
            },
        ]

    def _retrieve(self, vector_results, keyword_results, vector_weight, keyword_weight):
        retriever = HybridRetriever(
            FakeVectorStore(vector_results),
            FakeKeywordSearcher(keyword_results),
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
        )
        return retriever.retrieve(
            query="React",
            profile_id="demo",
            query_embedding=[0.0],
            max_chunks=10,
            min_score=0.0,
        )

    def test_tuned_weights_rank_correct_document_first(self, vector_results, keyword_results):
        """At the fixed 0.8/0.2 weights, the semantically-relevant chunk ranks #1."""
        results = self._retrieve(vector_results, keyword_results, 0.8, 0.2)

        assert results[0]["id"] == "resume-1"
        assert results[0]["metadata"]["source_id"] == "resume"

    def test_fifty_fifty_reproduces_the_bug(self, vector_results, keyword_results):
        """Locks in the reproduction: at 50/50 the keyword-stuffed wrong doc wins."""
        results = self._retrieve(vector_results, keyword_results, 0.5, 0.5)

        assert results[0]["id"] == "readme-1"
        assert results[0]["metadata"]["source_id"] == "readme"

    def test_blended_score_uses_weights(self, vector_results, keyword_results):
        """Blended score equals weight*normalized-vector + weight*normalized-keyword."""
        results = self._retrieve(vector_results, keyword_results, 0.8, 0.2)
        resume = next(r for r in results if r["id"] == "resume-1")

        # vector normalized: 0.85/0.85 = 1.0 ; keyword normalized: 3.0/9.0 = 0.3333
        expected = 0.8 * 1.0 + 0.2 * (3.0 / 9.0)
        assert resume["score"] == pytest.approx(expected)

    def test_pure_vector_weight_ignores_keyword(self, vector_results, keyword_results):
        """A zero keyword weight makes ranking depend only on vector similarity."""
        results = self._retrieve(vector_results, keyword_results, 1.0, 0.0)

        assert results[0]["id"] == "resume-1"
        # keyword_score is still computed (resume's normalized BM25 = 3.0/9.0)...
        assert results[0]["keyword_score"] == pytest.approx(3.0 / 9.0)
        # ...but with weight 0 it contributes nothing, so the score is pure vector (1.0).
        assert results[0]["score"] == pytest.approx(1.0)

    def test_pure_keyword_weight_ignores_vector(self, vector_results, keyword_results):
        """A zero vector weight makes ranking depend only on BM25 keyword score."""
        results = self._retrieve(vector_results, keyword_results, 0.0, 1.0)

        assert results[0]["id"] == "readme-1"

    def test_empty_results_do_not_crash(self):
        """Empty vector and keyword results return [] without dividing by zero."""
        results = self._retrieve([], [], 0.8, 0.2)

        assert results == []

    def test_keyword_only_chunk_scores_zero_vector(self, keyword_results):
        """A chunk present only in keyword results gets vector_score 0.0, not a crash."""
        results = self._retrieve([], keyword_results, 0.8, 0.2)

        by_id = {r["id"]: r for r in results}
        assert by_id["readme-1"]["vector_score"] == 0.0
        assert by_id["readme-1"]["keyword_score"] > 0.0

    def test_min_score_filters_low_blended_scores(self, vector_results, keyword_results):
        """Chunks below min_score are dropped from the results."""
        # readme-1 blended score at 0.8/0.2 is ~0.671; set threshold above it.
        results = self._retrieve(vector_results, keyword_results, 0.8, 0.2)
        high = HybridRetriever(
            FakeVectorStore(vector_results),
            FakeKeywordSearcher(keyword_results),
            vector_weight=0.8,
            keyword_weight=0.2,
        ).retrieve(
            query="React", profile_id="demo", query_embedding=[0.0], max_chunks=10, min_score=0.7
        )

        assert any(r["id"] == "readme-1" for r in results)  # present with no threshold
        assert all(r["id"] != "readme-1" for r in high)  # filtered out at min_score=0.7
        assert all(r["score"] >= 0.7 for r in high)
