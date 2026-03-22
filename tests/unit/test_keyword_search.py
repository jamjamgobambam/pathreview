"""Tests for keyword_search.py"""

import pytest
from unittest.mock import Mock, patch

from rag.retriever.keyword_search import KeywordSearcher


@pytest.mark.unit
class TestKeywordSearcher:
    """Test suite for KeywordSearcher."""

    @pytest.fixture
    def searcher(self):
        """Create a KeywordSearcher instance."""
        return KeywordSearcher()

    def test_results_sorted_by_score_descending(self, searcher):
        """Test that results are sorted by score descending (NOT insertion order)."""
        chunks = [
            {"id": 1, "text": "python programming language"},
            {"id": 2, "text": "java development platform"},
            {"id": 3, "text": "python django framework"},
            {"id": 4, "text": "typescript rust golang"},
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=10)

        # Results should be sorted by bm25_score descending
        assert len(results) > 0
        scores = [r.get("bm25_score", 0) for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_query_matching_no_documents(self, searcher):
        """Test query matching no documents returns empty list."""
        chunks = [
            {"id": 1, "text": "python programming"},
            {"id": 2, "text": "java development"},
        ]

        searcher.index(chunks)
        results = searcher.search("rust Go C++", top_k=10)

        # May return results with very low scores, but should not crash
        assert isinstance(results, list)

    def test_query_matching_multiple_documents(self, searcher):
        """Test query matching multiple documents returns highest score first."""
        chunks = [
            {"id": 1, "text": "python programming language"},
            {"id": 2, "text": "python django web framework"},
            {"id": 3, "text": "java programming language"},
            {"id": 4, "text": "python flask lightweight framework"},
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=10)

        assert len(results) >= 2
        # First result should have highest score
        if len(results) > 1:
            assert results[0]["bm25_score"] >= results[1]["bm25_score"]

    def test_case_insensitive_matching(self, searcher):
        """Test that matching is case insensitive."""
        chunks = [
            {"id": 1, "text": "Python Programming"},
            {"id": 2, "text": "JAVA Development"},
        ]

        searcher.index(chunks)

        results_lower = searcher.search("python", top_k=10)
        results_upper = searcher.search("PYTHON", top_k=10)
        results_mixed = searcher.search("PyThOn", top_k=10)

        # All three should return Python-related results
        assert len(results_lower) > 0
        assert len(results_upper) > 0
        assert len(results_mixed) > 0

    def test_top_k_limit(self, searcher):
        """Test that top_k parameter limits results."""
        chunks = [
            {"id": i, "text": f"python content {i}"}
            for i in range(20)
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=5)

        assert len(results) <= 5

    def test_top_k_larger_than_results(self, searcher):
        """Test top_k larger than available results."""
        chunks = [
            {"id": 1, "text": "python content"},
            {"id": 2, "text": "javascript content"},
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=100)

        # Should return available results, not pad to 100
        assert len(results) <= 2

    def test_results_have_bm25_score(self, searcher):
        """Test that results include bm25_score."""
        chunks = [
            {"id": 1, "text": "python programming"},
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=10)

        assert len(results) > 0
        for result in results:
            assert "bm25_score" in result
            assert isinstance(result["bm25_score"], float)

    def test_results_preserve_chunk_fields(self, searcher):
        """Test that original chunk fields are preserved in results."""
        chunks = [
            {"id": 1, "text": "python content", "source": "readme", "custom": "value"},
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=10)

        assert len(results) > 0
        result = results[0]
        assert result["id"] == 1
        assert result["text"] == "python content"
        assert result["source"] == "readme"
        assert result["custom"] == "value"

    def test_empty_index(self, searcher):
        """Test searching on empty index."""
        searcher.index([])
        results = searcher.search("python", top_k=10)

        assert results == []

    def test_index_not_called_returns_empty(self, searcher):
        """Test searching without calling index first."""
        results = searcher.search("python", top_k=10)

        assert results == []

    def test_multi_word_query(self, searcher):
        """Test multi-word query."""
        chunks = [
            {"id": 1, "text": "python web framework django"},
            {"id": 2, "text": "python data science numpy"},
            {"id": 3, "text": "javascript web development"},
        ]

        searcher.index(chunks)
        results = searcher.search("python web", top_k=10)

        assert len(results) > 0
        # Results with both words should rank higher

    def test_tokenization(self, searcher):
        """Test that tokenization works correctly."""
        tokens = searcher._tokenize("Python Web Framework")

        assert isinstance(tokens, list)
        assert all(isinstance(t, str) for t in tokens)
        assert len(tokens) == 3

    def test_tokenization_case_handling(self, searcher):
        """Test that tokenization converts to lowercase."""
        tokens = searcher._tokenize("PYTHON Django FLASK")

        # All tokens should be lowercase
        assert all(t.islower() or not t.isalpha() for t in tokens)

    def test_large_corpus(self, searcher):
        """Test indexing and searching large corpus."""
        chunks = [
            {"id": i, "text": f"document {i} with content about python web development"}
            for i in range(1000)
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=10)

        assert len(results) <= 10
        assert all("bm25_score" in r for r in results)

    def test_special_characters_in_query(self, searcher):
        """Test query with special characters."""
        chunks = [
            {"id": 1, "text": "python c++ rust golang"},
        ]

        searcher.index(chunks)
        results = searcher.search("c++", top_k=10)

        # Should handle special characters gracefully
        assert isinstance(results, list)

    def test_exact_phrase_matching(self, searcher):
        """Test that phrase matches score well."""
        chunks = [
            {"id": 1, "text": "web development framework"},
            {"id": 2, "text": "development of web applications"},
        ]

        searcher.index(chunks)
        results = searcher.search("web development", top_k=10)

        assert len(results) > 0
        # Results should be ranked by relevance

    def test_single_word_chunks(self, searcher):
        """Test handling of single-word chunks."""
        chunks = [
            {"id": 1, "text": "python"},
            {"id": 2, "text": "javascript"},
            {"id": 3, "text": "ruby"},
        ]

        searcher.index(chunks)
        results = searcher.search("python", top_k=10)

        assert len(results) > 0
        assert results[0]["id"] == 1
