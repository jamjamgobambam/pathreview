"""Tests for hybrid.py

Showcases issue #34: HybridRetriever's linear vector/keyword score blend can
rank a chunk that merely repeats a technology name above a chunk that is
genuinely more relevant, because keyword repetition inflates the normalized
BM25 score enough to outweigh a real (but not maximal) vector-similarity gap.
This does NOT fix the issue -- it only demonstrates it, to motivate the
LLM re-ranking step this issue asks for.
"""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher


@pytest.mark.unit
class TestHybridRetrieverKeywordBias:
    """Demonstrates keyword repetition overriding a stronger vector-similarity signal."""

    @pytest.fixture
    def chunks(self) -> list[dict]:
        """A small realistic corpus: a keyword-stuffed off-topic chunk, a genuinely
        relevant chunk, and unrelated filler chunks so "kubernetes" is a rare,
        distinctive term (needed for BM25's IDF to behave realistically -- with
        too few chunks a term appearing in most of them gets a near-zero or
        negative IDF, which masks the effect this test is showcasing)."""
        return [
            {
                "id": "stuffed",
                # Repeats the query's tech name many times; otherwise unrelated content.
                "text": (
                    "kubernetes kubernetes kubernetes kubernetes kubernetes kubernetes "
                    "pizza toppings recipe with extra cheese"
                ),
                "metadata": {"source_id": "s1"},
            },
            {
                "id": "relevant",
                # Mentions the tech name once, in a coherent, genuinely on-topic sentence.
                "text": "our team migrated the payment service to a managed kubernetes cluster",
                "metadata": {"source_id": "s2"},
            },
            {
                "id": "filler1",
                "text": "built a responsive marketing website using react and tailwind css",
                "metadata": {"source_id": "s3"},
            },
            {
                "id": "filler2",
                "text": "wrote unit tests and integration tests for the billing microservice",
                "metadata": {"source_id": "s4"},
            },
            {
                "id": "filler3",
                "text": "designed a rest api for the mobile app backend using flask",
                "metadata": {"source_id": "s5"},
            },
        ]

    @pytest.fixture
    def mock_vector_store(self, chunks: list[dict]) -> Mock:
        """Mock VectorStore where 'relevant' is the stronger semantic match, but only
        by a realistic margin -- exactly the close-call case re-ranking should help with."""
        store = Mock()

        store.query.return_value = [
            {
                "id": "relevant",
                "text": chunks[1]["text"],
                "metadata": chunks[1]["metadata"],
                "score": 0.9,
            },
            {
                "id": "stuffed",
                "text": chunks[0]["text"],
                "metadata": chunks[0]["metadata"],
                "score": 0.75,
            },
        ]

        collection = Mock()
        collection.get.return_value = {
            "ids": [c["id"] for c in chunks],
            "documents": [c["text"] for c in chunks],
            "metadatas": [c["metadata"] for c in chunks],
        }
        store.get_collection.return_value = collection

        return store

    @pytest.fixture
    def retriever(self, mock_vector_store: Mock) -> HybridRetriever:
        """HybridRetriever with default weights (vector_weight=0.7, keyword_weight=0.3)."""
        return HybridRetriever(mock_vector_store, KeywordSearcher())

    def test_keyword_stuffing_can_outrank_the_more_relevant_chunk(
        self, retriever: HybridRetriever
    ) -> None:
        """Showcases the bug driving issue #34: keyword repetition flips the ranking.

        "relevant" has the stronger vector-similarity score (0.9 vs 0.75 raw,
        i.e. normalized vector_score of 1.0 vs ~0.83), which is what a human
        reviewer would judge as the better chunk for this query -- a realistic,
        close-call gap, not a landslide. But "stuffed" repeats the query's tech
        name 6x, so its normalized BM25 score dominates its result set (1.0)
        enough that, blended with the default 0.7/0.3 weights, it ends up
        ranked ABOVE "relevant" -- exactly the "keyword search might rank a
        document higher just because it contains a specific keyword multiple
        times" problem this issue describes. This test only documents the
        behavior; it does not fix it.
        """
        results = retriever.retrieve(
            query="kubernetes deployment",
            profile_id="profile1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=5,
            min_score=0.0,
        )

        by_id = {r["id"]: r for r in results}
        for r in results:
            print(
                f'{r["id"]}: blended={r["score"]:.3f}, '
                f'vector={r["vector_score"]:.3f}, keyword={r["keyword_score"]:.3f}'
            )

        # Vector search alone correctly prefers "relevant".
        assert by_id["relevant"]["vector_score"] > by_id["stuffed"]["vector_score"]

        # But the blended score flips the ranking: the keyword-stuffed, off-topic
        # chunk ends up ranked first (of the two candidates vector search actually
        # surfaced) despite being the weaker semantic match.
        candidates_in_rank_order = [r["id"] for r in results if r["id"] in ("stuffed", "relevant")]
        assert candidates_in_rank_order[0] == "stuffed"
        assert by_id["stuffed"]["score"] > by_id["relevant"]["score"]
