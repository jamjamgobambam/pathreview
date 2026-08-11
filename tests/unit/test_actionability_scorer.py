"""Tests for actionability_scorer.py"""

import pytest

from rag.evaluator.actionability_scorer import ActionabilityScorer


@pytest.mark.unit
class TestActionabilityScorer:
    """Test suite for ActionabilityScorer."""

    @pytest.fixture
    def scorer(self):
        """Create an ActionabilityScorer instance."""
        return ActionabilityScorer()

    def test_empty_feedback_returns_zero(self, scorer):
        """Empty feedback is not actionable."""
        assert scorer.score("") == 0.0
        assert scorer.score("   ") == 0.0

    def test_vague_feedback_scores_low(self, scorer):
        """Generic praise without next steps scores low."""
        feedback = "This portfolio looks nice overall and the work is interesting."
        score = scorer.score(feedback)
        assert 0.0 <= score <= 1.0
        assert score < 0.4

    def test_actionable_feedback_scores_high(self, scorer):
        """Concrete recommendations score high."""
        feedback = (
            "Add impact metrics to each project README. "
            "Include latency numbers from your load tests. "
            "Consider rewriting the skills section to highlight Python and FastAPI.\n"
            "- Link your best repository from the resume.\n"
            "- Provide a short case study with measurable outcomes."
        )
        score = scorer.score(feedback)
        assert score > 0.5

    def test_score_is_bounded(self, scorer):
        """Score always stays within 0-1."""
        feedback = "Add include consider replace update improve " * 20
        score = scorer.score(feedback)
        assert 0.0 <= score <= 1.0
