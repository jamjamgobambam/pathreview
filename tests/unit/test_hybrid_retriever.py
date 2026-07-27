from unittest.mock import MagicMock

import pytest

from rag.retriever.hybrid import HybridRetriever

QUERY = "leadership and team management experience"

GENUINE_TEXT = "Led a team of 4 engineers on the checkout redesign project"
DECOY_TEXT = "Managed weekend shift schedule at campus bakery"


@pytest.mark.unit
class TestHybridRetriever:

    @pytest.fixture
    def mock_vector_store(self) -> MagicMock:
        store = MagicMock()
        store.query.return_value = [
            {"id": "genuine-1", "text": GENUINE_TEXT, "metadata": {}, "score": 0.55},
            {"id": "decoy-1", "text": DECOY_TEXT, "metadata": {}, "score": 0.82},
        ]
        store.get_collection.return_value.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        return store

    @pytest.fixture
    def mock_keyword_searcher(self) -> MagicMock:
        searcher = MagicMock()
        searcher.search.return_value = [
            {"id": "decoy-1", "text": DECOY_TEXT, "bm25_score": 6.4},
            {"id": "genuine-1", "text": GENUINE_TEXT, "bm25_score": 3.1},
        ]
        return searcher

    @pytest.fixture
    def retriever(
        self, mock_vector_store: MagicMock, mock_keyword_searcher: MagicMock
    ) -> HybridRetriever:
        return HybridRetriever(mock_vector_store, mock_keyword_searcher)

    def test_decoy_outranks_genuine_match(self, retriever: HybridRetriever) -> None:
        """Reproduces the gap in issue #34: hybrid scoring has no semantic
        check, so a chunk that merely shares vocabulary/embedding-space
        proximity with the query can outrank a chunk that actually answers
        it. Here 'campus bakery shift scheduling' outscores 'led an
        engineering team' for a query about leadership/team management,
        because both vector and BM25 scores are lexical/embedding proxies,
        not judgments of whether the chunk answers the query.
        """
        results = retriever.retrieve(
            query=QUERY,
            profile_id="test-profile",
            query_embedding=[0.1] * 8,
        )

        result_ids = [r["id"] for r in results]
        assert "decoy-1" in result_ids
        assert "genuine-1" in result_ids

        decoy_score = next(r["score"] for r in results if r["id"] == "decoy-1")
        genuine_score = next(r["score"] for r in results if r["id"] == "genuine-1")

        # Current retrieve() has no mechanism to catch this: the topically
        # irrelevant decoy wins purely on blended keyword/vector score.
        assert decoy_score >= genuine_score
