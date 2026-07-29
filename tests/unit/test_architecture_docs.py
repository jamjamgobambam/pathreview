"""Reproduction test for issue #36: ARCHITECTURE.md doesn't explain the
hybrid retrieval scoring formula.

This test documents the doc gap by asserting that docs/ARCHITECTURE.md
contains a "Hybrid Retrieval Scoring" subsection describing the blending
formula, default weights, normalization step, and a worked example. It
currently fails, which reproduces the issue; it should pass once the
architecture doc is updated.
"""

from pathlib import Path

import pytest

ARCHITECTURE_DOC = Path(__file__).resolve().parents[2] / "docs" / "ARCHITECTURE.md"


@pytest.mark.unit
class TestArchitectureDocHybridScoring:
    """Test suite reproducing issue #36 (missing hybrid scoring docs)."""

    @pytest.fixture
    def doc_text(self):
        return ARCHITECTURE_DOC.read_text(encoding="utf-8")

    def test_has_hybrid_retrieval_scoring_subsection(self, doc_text):
        """The doc should have a dedicated subsection on hybrid scoring."""
        assert "Hybrid Retrieval Scoring" in doc_text

    def test_documents_default_weights(self, doc_text):
        """The doc should state the default vector/keyword weights (0.7/0.3)."""
        assert "0.7" in doc_text
        assert "0.3" in doc_text

    def test_documents_normalization_step(self, doc_text):
        """The doc should explain the max-normalization step."""
        assert "normaliz" in doc_text.lower()

    def test_documents_min_score_cutoff(self, doc_text):
        """The doc should mention the min_score cutoff behavior."""
        assert "min_score" in doc_text
