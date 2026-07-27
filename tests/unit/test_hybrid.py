"""Tests for hybrid.py"""

from unittest.mock import Mock

import pytest

from rag.retriever.hybrid import HybridRetriever


@pytest.mark.unit
class TestHybridRetriever:
    """Test suite for HybridRetriever."""

    @pytest.fixture
    def mock_vector_store(self) -> Mock:
        """A VectorStore stand-in. retrieve() also calls
        get_collection().get() internally (for keyword indexing), so stub
        that out too even though these tests configure keyword hits
        directly via mock_keyword_searcher instead."""
        store = Mock()
        store.get_collection.return_value.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        return store

    @pytest.fixture
    def mock_keyword_searcher(self) -> Mock:
        return Mock()

    @pytest.fixture
    def retriever(self, mock_vector_store: Mock, mock_keyword_searcher: Mock) -> HybridRetriever:
        """Create a HybridRetriever instance with mocked dependencies."""
        return HybridRetriever(mock_vector_store, mock_keyword_searcher)

    def test_chunk_in_both_sources_ranks_first(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that a chunk found by both vector and keyword search
        outranks chunks found by only one source."""
        mock_vector_store.query.return_value = [
            {"id": 1, "text": "python programming language", "score": 0.82, "metadata": {}},
            {"id": 4, "text": "typescript rust golang", "score": 0.75, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = [
            {"id": 3, "text": "python django framework", "bm25_score": 6.0},
            {"id": 1, "text": "python programming language", "bm25_score": 3.0},
        ]

        results = retriever.retrieve(
            query="python web development",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.0,
        )

        ids_in_order = [r["id"] for r in results]
        assert ids_in_order[0] == 1

    def test_default_weights_can_rank_an_irrelevant_chunk_above_a_relevant_one(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test the mechanical blend problem this issue is about: a chunk
        that only resembles the query in embedding space ("typescript rust
        golang") can outrank a chunk found via an exact keyword match
        ("python django framework"), purely because the default weights
        favor vector_score (0.7) over keyword_score (0.3) -- no semantic
        judgment is involved.
        """
        mock_vector_store.query.return_value = [
            {"id": 1, "text": "python programming language", "score": 0.82, "metadata": {}},
            {"id": 4, "text": "typescript rust golang", "score": 0.75, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = [
            {"id": 3, "text": "python django framework", "bm25_score": 6.0},
            {"id": 1, "text": "python programming language", "bm25_score": 3.0},
        ]

        results = retriever.retrieve(
            query="python web development",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.0,
        )

        ids_in_order = [r["id"] for r in results]
        # id 4 has nothing to do with the query but ranks above id 3, which
        # actually contains "python" + "framework" -- blend math alone
        # decides the order today.
        assert ids_in_order.index(4) < ids_in_order.index(3)

    def test_chunk_only_in_vector_results_is_included(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that a chunk found only by vector search still comes back,
        with keyword_score of 0."""
        mock_vector_store.query.return_value = [
            {"id": 2, "text": "java development platform", "score": 0.5, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="platform engineering",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.0,
        )

        assert len(results) == 1
        assert results[0]["id"] == 2
        assert results[0]["keyword_score"] == 0.0
        assert results[0]["vector_score"] == pytest.approx(1.0)

    def test_chunk_only_in_keyword_results_is_included(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that a chunk found only by keyword search still comes back,
        with vector_score of 0."""
        mock_vector_store.query.return_value = []
        mock_keyword_searcher.search.return_value = [
            {"id": 3, "text": "python django framework", "bm25_score": 4.0},
        ]

        results = retriever.retrieve(
            query="django framework",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.0,
        )

        assert len(results) == 1
        assert results[0]["id"] == 3
        assert results[0]["vector_score"] == 0.0
        assert results[0]["keyword_score"] == pytest.approx(1.0)

    def test_chunk_missing_from_both_sources_is_excluded(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that only chunks returned by at least one source appear in
        the results -- e.g. "java development platform" never shows up if
        neither search surfaces it."""
        mock_vector_store.query.return_value = [
            {"id": 1, "text": "python programming language", "score": 0.9, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = [
            {"id": 1, "text": "python programming language", "bm25_score": 2.0},
        ]

        results = retriever.retrieve(
            query="python",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.0,
        )

        ids = [r["id"] for r in results]
        assert ids == [1]
        assert 2 not in ids

    def test_min_score_filters_low_scoring_chunks(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that chunks below min_score are dropped from the results."""
        mock_vector_store.query.return_value = [
            {"id": 1, "text": "python programming language", "score": 0.9, "metadata": {}},
            {"id": 4, "text": "typescript rust golang", "score": 0.1, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="python",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.5,
        )

        ids = [r["id"] for r in results]
        assert ids == [1]

    def test_max_chunks_limits_results(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that max_chunks limits the number of returned results to
        the top-scoring chunks."""
        mock_vector_store.query.return_value = [
            {"id": 1, "text": "python programming language", "score": 0.9, "metadata": {}},
            {"id": 2, "text": "java development platform", "score": 0.8, "metadata": {}},
            {"id": 3, "text": "python django framework", "score": 0.7, "metadata": {}},
            {"id": 4, "text": "typescript rust golang", "score": 0.6, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="python",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            max_chunks=2,
            min_score=0.0,
        )

        assert len(results) == 2
        assert [r["id"] for r in results] == [1, 2]

    def test_empty_vector_and_keyword_results_returns_empty_list(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that retrieve() returns an empty list when neither source
        has any hits."""
        mock_vector_store.query.return_value = []
        mock_keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="python",
            profile_id="p1",
            query_embedding=[0.0] * 5,
        )

        assert results == []

    def test_results_preserve_chunk_text(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """Test that the original chunk text is preserved in results."""
        mock_vector_store.query.return_value = [
            {"id": 3, "text": "python django framework", "score": 0.8, "metadata": {}},
        ]
        mock_keyword_searcher.search.return_value = []

        results = retriever.retrieve(
            query="django",
            profile_id="p1",
            query_embedding=[0.0] * 5,
            min_score=0.0,
        )

        assert results[0]["text"] == "python django framework"

    def test_retrieve_has_no_reranker_parameter(
        self, retriever: HybridRetriever, mock_vector_store: Mock, mock_keyword_searcher: Mock
    ) -> None:
        """retrieve() should accept an optional `reranker` that gets a
        chance to re-score/re-order candidates before truncation. Today it
        doesn't -- passing one raises TypeError.
        """
        mock_vector_store.query.return_value = []
        mock_keyword_searcher.search.return_value = []
        fake_reranker = Mock()

        with pytest.raises(TypeError):
            retriever.retrieve(  # type: ignore[call-arg]  # intentional: proves the gap
                query="python",
                profile_id="p1",
                query_embedding=[0.0] * 5,
                reranker=fake_reranker,
            )

    def test_reranker_module_does_not_exist_yet(self) -> None:
        """rag/retriever/reranker.py (the new LLMReranker class called for
        in issue #34) hasn't been created yet.
        """
        with pytest.raises(ModuleNotFoundError):
            import rag.retriever.reranker  # noqa: F401
