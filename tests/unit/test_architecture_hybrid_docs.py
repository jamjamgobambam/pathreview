"""Reproduction for issue #36: ARCHITECTURE.md missing hybrid scoring docs.

These tests encode the documentation gap. They fail today (Week 8) because
docs/ARCHITECTURE.md only mentions hybrid retrieval at a high level. They
should pass after Week 9 when the scoring formula, defaults, and an example
are added under the RAG System section.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"


@pytest.fixture(scope="module")
def architecture_text() -> str:
    assert ARCHITECTURE.exists(), f"Missing {ARCHITECTURE}"
    return ARCHITECTURE.read_text(encoding="utf-8")


@pytest.mark.unit
class TestArchitectureHybridScoringDocs:
    """Issue #36 reproduction: expected docs content is currently absent."""

    def test_documents_default_vector_and_keyword_weights(self, architecture_text: str) -> None:
        """ARCHITECTURE.md should name the default blend weights from HybridRetriever."""
        lower = architecture_text.lower()
        assert "0.7" in architecture_text or "vector_weight" in lower, (
            "docs/ARCHITECTURE.md does not document vector_weight default 0.7 "
            "(see rag/retriever/hybrid.py HybridRetriever.__init__)"
        )
        assert "0.3" in architecture_text and (
            "keyword_weight" in lower or "bm25" in lower or "keyword" in lower
        ), "docs/ARCHITECTURE.md does not document keyword_weight default 0.3"

    def test_documents_score_normalization_and_blend_formula(self, architecture_text: str) -> None:
        """ARCHITECTURE.md should explain per-channel max-normalization + weighted sum."""
        lower = architecture_text.lower()
        mentions_normalize = "normal" in lower or "max" in lower
        mentions_blend = "blend" in lower or "weight" in lower or "formula" in lower
        assert mentions_normalize and mentions_blend, (
            "docs/ARCHITECTURE.md does not explain how vector/BM25 scores are "
            "normalized and blended (see HybridRetriever.retrieve)"
        )

    def test_documents_min_score_threshold(self, architecture_text: str) -> None:
        """ARCHITECTURE.md should document the default min_score filter (0.3)."""
        lower = architecture_text.lower()
        assert "min_score" in lower or (
            "threshold" in lower and "0.3" in architecture_text
        ), "docs/ARCHITECTURE.md does not document min_score=0.3 filtering"
