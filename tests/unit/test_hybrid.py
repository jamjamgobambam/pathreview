"""Tests for hybrid.py

Confirms the fix for issue #34 follow-on bug: HybridRetriever was blending in
a keyword_score that was always 0.0, because KeywordSearcher.index() was never
called before KeywordSearcher.search() in HybridRetriever.retrieve(). Now that
hybrid.py indexes all_chunks before searching, keyword_score should reflect
actual BM25 relevance.
"""

import logging
from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever
from rag.retriever.keyword_search import KeywordSearcher


@pytest.mark.unit
class TestHybridRetrieverKeywordScoring:
    """Reproduces keyword_score always being 0.0 in HybridRetriever."""

    @pytest.fixture
    def chunks(self) -> list[dict]:
        """Sample chunks: one keyword-heavy, one keyword-sparse but relevant, one irrelevant."""
        return [
            {
                "id": "c1",
                "text": "kubernetes kubernetes kubernetes deployment scaling kubernetes",
                "metadata": {"source_id": "s1"},
            },
            {
                "id": "c2",
                "text": "container orchestration platform used for scaling deployment",
                "metadata": {"source_id": "s2"},
            },
            {
                "id": "c3",
                "text": "grandmother's chocolate cake recipe with frosting",
                "metadata": {"source_id": "s3"},
            },
        ]

    @pytest.fixture
    def mock_vector_store(self, chunks: list[dict]) -> Mock:
        """Mock VectorStore returning fixed vector-similarity hits and full corpus."""
        store = Mock()

        # Vector search "finds" c2 and c3 as semantically similar to the query,
        # deliberately excluding the keyword-heavy c1.
        store.query.return_value = [
            {
                "id": "c2",
                "text": chunks[1]["text"],
                "metadata": chunks[1]["metadata"],
                "score": 0.9,
            },
            {
                "id": "c3",
                "text": chunks[2]["text"],
                "metadata": chunks[2]["metadata"],
                "score": 0.4,
            },
        ]

        # get_collection(...).get(...) returns the full corpus, mirroring ChromaDB's shape.
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
        """HybridRetriever wired with a real (un-indexed) KeywordSearcher."""
        return HybridRetriever(mock_vector_store, KeywordSearcher())

    def test_keyword_score_reflects_bm25_relevance(
        self, retriever: HybridRetriever, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Confirms the fix: keyword_score now reflects real BM25 relevance.

        HybridRetriever.retrieve() now indexes all_chunks before calling
        keyword_searcher.search(), so BM25 scores differentiate between the
        keyword-heavy chunk ("c1"), the keyword-sparse-but-relevant chunk
        ("c2"), and the keyword-irrelevant chunk ("c3").
        """
        with caplog.at_level(logging.WARNING):
            results = retriever.retrieve(
                query="kubernetes deployment",
                profile_id="profile1",
                query_embedding=[0.1, 0.2, 0.3],
                max_chunks=5,
                min_score=0.0,
            )
        for r in results:
            print(
                f'{r["id"]}: keyword_score={r["keyword_score"]}, vector_score={r["vector_score"]}'
            )

        assert len(results) == 3  # c1 now surfaces via the keyword path
        assert "keyword_search_empty_index" not in caplog.text

        by_id = {r["id"]: r for r in results}

        # c1 repeats "kubernetes" heavily and contains "deployment" -> highest keyword score.
        assert by_id["c1"]["keyword_score"] > 0.0
        # c2 contains "deployment" only -> nonzero but lower than c1.
        assert 0.0 < by_id["c2"]["keyword_score"] < by_id["c1"]["keyword_score"]
        # c3 shares no terms with the query -> BM25 contributes nothing.
        assert by_id["c3"]["keyword_score"] == 0.0

    def test_keyword_searcher_indexed_on_retrieve(
        self, retriever: HybridRetriever, chunks: list[dict]
    ) -> None:
        """Confirms the fix: retrieve() now indexes the collection's chunks."""
        assert retriever.keyword_searcher.bm25 is None
        assert retriever.keyword_searcher.chunks == []

        retriever.retrieve(
            query="kubernetes deployment",
            profile_id="profile1",
            query_embedding=[0.1, 0.2, 0.3],
            max_chunks=5,
            min_score=0.0,
        )

        # Now indexed with the full corpus fetched via _get_all_chunks().
        assert retriever.keyword_searcher.bm25 is not None
        assert {c["id"] for c in retriever.keyword_searcher.chunks} == {c["id"] for c in chunks}
