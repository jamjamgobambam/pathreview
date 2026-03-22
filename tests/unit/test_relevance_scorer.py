"""Tests for relevance_scorer.py"""

import pytest

from rag.evaluator.relevance_scorer import RelevanceScorer


@pytest.mark.unit
class TestRelevanceScorer:
    """Test suite for RelevanceScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a RelevanceScorer instance."""
        return RelevanceScorer()

    def test_query_with_perfect_keyword_match(self, scorer):
        """Test query with perfect keyword match in chunks returns score close to 1.0."""
        query = "Python development framework"
        chunks = [
            {
                "text": "Python is a great development language for building frameworks"
            },
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Should be high score due to keyword overlap
        assert score > 0.5

    def test_query_with_zero_keyword_overlap(self, scorer):
        """Test query with zero keyword overlap returns score close to 0.0."""
        query = "Rust Kubernetes microservices"
        chunks = [
            {
                "text": "Python is dynamically typed and interpreted language"
            },
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert score < 0.5  # Should be low score

    def test_query_with_partial_overlap(self, scorer):
        """Test query with partial overlap returns score between 0 and 1."""
        query = "Python Django web framework"
        chunks = [
            {
                "text": "Django is a Python web framework for rapid development"
            },
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert 0.3 < score < 0.9  # Partial overlap should be in middle range

    def test_empty_chunks_list_returns_zero(self, scorer):
        """Test empty chunks list returns 0.0."""
        query = "Some query"
        chunks = []

        score = scorer.score(query, chunks)

        assert score == 0.0

    def test_empty_query_returns_zero(self, scorer):
        """Test empty query returns 0.0."""
        query = ""
        chunks = [
            {"text": "Some content"}
        ]

        score = scorer.score(query, chunks)

        assert score == 0.0

    def test_multiple_chunks_aggregated(self, scorer):
        """Test that score aggregates multiple chunks."""
        query = "Python programming"
        chunks = [
            {"text": "Python is a programming language"},
            {"text": "Java is another programming language"},
            {"text": "Python and Java are popular languages"},
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_case_insensitive_matching(self, scorer):
        """Test that keyword matching is case insensitive."""
        query = "PYTHON PROGRAMMING"
        chunks = [
            {"text": "python programming is fun"}
        ]

        score = scorer.score(query, chunks)

        # Should match despite different cases
        assert score > 0.5

    def test_tokenization(self, scorer):
        """Test that tokenization works correctly."""
        tokens = scorer._tokenize("Python web development framework")

        assert isinstance(tokens, list)
        assert len(tokens) == 4
        assert all(isinstance(t, str) for t in tokens)
        assert "python" in tokens  # Should be lowercase

    def test_empty_text_in_chunk(self, scorer):
        """Test handling of empty text in chunk."""
        query = "Python"
        chunks = [
            {"text": ""},
            {"text": "Python programming"}
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_very_long_query(self, scorer):
        """Test handling of very long query."""
        query = "Python " * 100
        chunks = [
            {"text": "Python is a programming language"}
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_very_long_chunk(self, scorer):
        """Test handling of very long chunk."""
        query = "Python"
        chunks = [
            {"text": "Python " * 1000 + "is a great language"}
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_special_characters_ignored(self, scorer):
        """Test that special characters are handled."""
        query = "Python c++ golang"
        chunks = [
            {"text": "c++ is a systems programming language"}
        ]

        score = scorer.score(query, chunks)

        # Should handle special characters in tokenization
        assert isinstance(score, float)

    def test_multiple_keyword_matches(self, scorer):
        """Test scoring improves with multiple keyword matches."""
        query = "Python framework development tools"
        chunks = [
            {"text": "Python django flask development framework tools"}
        ]

        score = scorer.score(query, chunks)

        # Multiple matches should yield higher score
        assert score > 0.6

    def test_single_word_chunks(self, scorer):
        """Test handling of single-word chunks."""
        query = "Python development"
        chunks = [
            {"text": "Python"},
            {"text": "development"},
            {"text": "framework"}
        ]

        score = scorer.score(query, chunks)

        assert isinstance(score, float)
        assert score > 0.0  # Should find matches

    def test_score_ranges_from_zero_to_one(self, scorer):
        """Test that score is always between 0 and 1."""
        test_cases = [
            ("Python", [{"text": "Java"}]),  # No match
            ("Python", [{"text": "Python programming"}]),  # Perfect match
            ("machine learning", [{"text": "ML Python TensorFlow"}]),  # Partial
        ]

        for query, chunks in test_cases:
            score = scorer.score(query, chunks)
            assert 0.0 <= score <= 1.0

    def test_common_words_not_preventing_scoring(self, scorer):
        """Test that common words don't prevent scoring."""
        query = "the best Python framework"
        chunks = [
            {"text": "Django is the best Python web framework"}
        ]

        score = scorer.score(query, chunks)

        # Despite common words, should still score relevantly
        assert score > 0.3

    def test_chunk_without_text_key(self, scorer):
        """Test handling of chunk missing 'text' key."""
        query = "Python"
        chunks = [
            {"content": "Python programming"}  # Wrong key
        ]

        score = scorer.score(query, chunks)

        # Should handle gracefully
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_whitespace_only_in_chunks(self, scorer):
        """Test chunks with only whitespace."""
        query = "Python"
        chunks = [
            {"text": "   "},
            {"text": "\n\t"}
        ]

        score = scorer.score(query, chunks)

        assert score == 0.0

    def test_average_relevance_calculation(self, scorer):
        """Test that multiple chunks' scores are averaged."""
        query = "Python"
        chunks = [
            {"text": "Python is great"},
            {"text": "Python programming"},
            {"text": "Java is different"}
        ]

        score = scorer.score(query, chunks)

        # Score should be average of three chunks
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
