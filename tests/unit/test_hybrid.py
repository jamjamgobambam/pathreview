"""Tests for hybrid.py."""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever


@pytest.mark.unit
class TestHybridRetriever:
    """Test suite for HybridRetriever."""

    @pytest.fixture
    def vector_store(self):
        """Create a mocked VectorStore."""
        return Mock()

    @pytest.fixture
    def keyword_searcher(self):
        """Create a mocked KeywordSearcher."""
        return Mock()

    @pytest.fixture
    def retriever(self, vector_store, keyword_searcher):
        """Create a HybridRetriever with mocked dependencies."""
        retriever = HybridRetriever(
            vector_store=vector_store,
            keyword_searcher=keyword_searcher,
        )

        # Prevent access to a real ChromaDB collection.
        retriever._get_all_chunks = Mock(return_value=[])

        return retriever

    def test_chunk_found_by_both_searches_ranks_highest(
        self,
        retriever,
        vector_store,
        keyword_searcher,
    ):
        """Test a chunk found by both searches receives both scores."""
        vector_store.query.return_value = [
            {
                "id": "shared_chunk",
                "text": "Python machine learning experience",
                "metadata": {},
                "score": 1.0,
            },
            {
                "id": "vector_only_chunk",
                "text": "Software engineering experience",
                "metadata": {},
                "score": 0.8,
            },
        ]

        keyword_searcher.search.return_value = [
            {
                "id": "shared_chunk",
                "text": "Python machine learning experience",
                "metadata": {},
                "bm25_score": 5.0,
            },
            {
                "id": "keyword_only_chunk",
                "text": "Python programming",
                "metadata": {},
                "bm25_score": 4.0,
            },
        ]

        results = retriever.retrieve(
            query="Python machine learning",
            profile_id="test",
            query_embedding=[0.1, 0.2],
            min_score=0.0,
        )

        assert results[0]["id"] == "shared_chunk"
        assert results[0]["vector_score"] == pytest.approx(1.0)
        assert results[0]["keyword_score"] == pytest.approx(1.0)
        assert results[0]["score"] == pytest.approx(1.0)

    def test_semantic_vector_chunk_should_outrank_keyword_only_chunk(
        self,
        retriever,
        vector_store,
        keyword_searcher,
    ):
        """Reproduce keyword-only chunk outranking a semantic vector chunk."""
        vector_store.query.return_value = [
            {
                "id": "strong_vector_anchor",
                "text": "Another highly ranked vector result",
                "metadata": {},
                "score": 1.0,
            },
            {
                "id": "semantic_chunk",
                "text": ("Built a forecasting model using historical weather data"),
                "metadata": {},
                "score": 0.4,
            },
        ]

        keyword_searcher.search.return_value = [
            {
                "id": "keyword_only_chunk",
                "text": "Python Python Python",
                "metadata": {},
                "bm25_score": 5.0,
            }
        ]

        results = retriever.retrieve(
            query="Python forecasting experience",
            profile_id="test",
            query_embedding=[0.1, 0.2],
            min_score=0.0,
        )

        result_ids = [result["id"] for result in results]

        assert result_ids.index("semantic_chunk") < result_ids.index("keyword_only_chunk")

    def test_keyword_score_boosts_weaker_vector_chunk_above_stronger_vector_chunk(
        self,
        retriever,
        vector_store,
        keyword_searcher,
    ):
        """Reproduce keyword score causing a weaker vector result to rank first."""

        vector_store.query.return_value = [
            {
                "id": "relevant_chunk",
                "text": "Built a weather forecasting model",
                "metadata": {},
                "score": 1.0,
            },
            {
                "id": "keyword_boosted_chunk",
                "text": "Python Python Python",
                "metadata": {},
                "score": 0.6,
            },
        ]

        keyword_searcher.search.return_value = [
            {
                "id": "keyword_boosted_chunk",
                "text": "Python Python Python",
                "metadata": {},
                "bm25_score": 5.0,
            }
        ]

        results = retriever.retrieve(
            query="Python weather forecasting experience",
            profile_id="test",
            query_embedding=[0.1, 0.2],
            min_score=0.0,
        )

        assert results[0]["id"] == "relevant_chunk"

    def test_results_below_min_score_are_removed(
        self,
        retriever,
        vector_store,
        keyword_searcher,
    ):
        """Test results below min_score are removed."""
        vector_store.query.return_value = [
            {
                "id": "strong_chunk",
                "text": "Strong semantic match",
                "metadata": {},
                "score": 1.0,
            },
            {
                "id": "weak_chunk",
                "text": "Weak semantic match",
                "metadata": {},
                "score": 0.2,
            },
        ]

        keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="semantic query",
            profile_id="test",
            query_embedding=[0.1, 0.2],
            min_score=0.3,
        )

        result_ids = [result["id"] for result in results]

        assert "strong_chunk" in result_ids
        assert "weak_chunk" not in result_ids

    def test_empty_search_results_return_empty_list(
        self,
        retriever,
        vector_store,
        keyword_searcher,
    ):
        """Test empty searches return an empty list."""
        vector_store.query.return_value = []
        keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="anything",
            profile_id="test",
            query_embedding=[0.1, 0.2],
        )

        assert results == []

    def test_max_chunks_limits_number_of_results(
        self,
        retriever,
        vector_store,
        keyword_searcher,
    ):
        """Test max_chunks limits the number of returned results."""
        vector_store.query.return_value = [
            {
                "id": "chunk_1",
                "text": "First result",
                "metadata": {},
                "score": 1.0,
            },
            {
                "id": "chunk_2",
                "text": "Second result",
                "metadata": {},
                "score": 0.9,
            },
            {
                "id": "chunk_3",
                "text": "Third result",
                "metadata": {},
                "score": 0.8,
            },
        ]

        keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="query",
            profile_id="test",
            query_embedding=[0.1, 0.2],
            max_chunks=2,
            min_score=0.0,
        )

        assert len(results) == 2
        assert results[0]["id"] == "chunk_1"
        assert results[1]["id"] == "chunk_2"
