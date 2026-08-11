"""Tests for required architecture documentation."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ARCHITECTURE_DOC = Path(__file__).resolve().parents[2] / "docs" / "ARCHITECTURE.md"


def test_hybrid_retrieval_scoring_is_documented() -> None:
    """Verify that the hybrid retrieval scoring behavior is documented."""
    content = ARCHITECTURE_DOC.read_text(encoding="utf-8")

    assert "Hybrid retrieval scoring" in content
    assert "normalized_vector_score" in content
    assert "normalized_keyword_score" in content
    assert "blended_score" in content
    assert "Vector similarity: `0.7`" in content
    assert "BM25 keyword relevance: `0.3`" in content
    assert "minimum score is `0.3`" in content
    assert "receives a score of `0`" in content
