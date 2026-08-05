"""Tests for the "Hybrid Retrieval Scoring" section of docs/ARCHITECTURE.md (issue #36).

TestArchitectureDocHybridScoring asserts the subsection exists and mentions the
blending formula, default weights, normalization step, and min_score cutoff.
These reproduced issue #36 by failing against the pre-fix doc.

TestArchitectureDocMatchesCode goes further and checks that what the doc claims
is actually true of HybridRetriever, so the prose can't drift away from
rag/retriever/hybrid.py without a test failing.
"""

import inspect
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rag.retriever.hybrid import HybridRetriever

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


@pytest.mark.unit
class TestArchitectureDocMatchesCode:
    """Guard against the documented scoring behavior drifting from hybrid.py.

    The four assertions above only check that the doc *mentions* the formula.
    These check that what it says is actually true of HybridRetriever, so the
    subsection can't silently go stale when defaults or blending change.
    """

    @pytest.fixture
    def doc_text(self):
        return ARCHITECTURE_DOC.read_text(encoding="utf-8")

    @pytest.fixture
    def retriever(self):
        """Build a HybridRetriever over mocked vector and keyword backends.

        The scores match the worked example in the architecture doc: C1 and C2
        are found by both searches, C3 only by vector, C4 only by BM25.
        """
        vector_store = MagicMock()
        vector_store.query.return_value = [
            {"id": "C1", "text": "c1", "metadata": {}, "score": 0.60},
            {"id": "C2", "text": "c2", "metadata": {}, "score": 0.42},
            {"id": "C3", "text": "c3", "metadata": {}, "score": 0.30},
        ]
        # _get_all_chunks() reads the collection directly; nothing to return.
        vector_store.get_collection.return_value.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }

        keyword_searcher = MagicMock()
        keyword_searcher.search.return_value = [
            {"id": "C2", "text": "c2", "bm25_score": 8.0},
            {"id": "C4", "text": "c4", "bm25_score": 4.0},
            {"id": "C1", "text": "c1", "bm25_score": 2.0},
        ]

        return HybridRetriever(vector_store, keyword_searcher)

    @staticmethod
    def _doc_line_for(doc_text: str, parameter: str) -> str:
        """Return the doc's parameter-table row mentioning the given parameter."""
        matches = [
            line for line in doc_text.splitlines() if f"`{parameter}`" in line and "|" in line
        ]
        assert matches, f"no parameter-table row documenting `{parameter}`"
        return matches[0]

    @pytest.mark.parametrize(
        ("parameter", "method"),
        [
            ("vector_weight", HybridRetriever.__init__),
            ("keyword_weight", HybridRetriever.__init__),
            ("max_chunks", HybridRetriever.retrieve),
            ("min_score", HybridRetriever.retrieve),
        ],
    )
    def test_documented_defaults_match_signature(self, doc_text, parameter, method):
        """Each default in the doc's parameter table matches the actual signature."""
        actual_default = inspect.signature(method).parameters[parameter].default

        assert str(actual_default) in self._doc_line_for(
            doc_text, parameter
        ), f"doc row for `{parameter}` does not state its real default {actual_default!r}"

    def test_worked_example_scores_match_real_blending(self, retriever):
        """Running the doc's worked example through HybridRetriever reproduces its numbers."""
        results = retriever.retrieve("testing experience", "p1", [0.1, 0.2, 0.3])

        scores = {r["id"]: r["score"] for r in results}
        assert scores == pytest.approx({"C2": 0.790, "C1": 0.775, "C3": 0.350})

    def test_worked_example_ranking_matches_doc(self, retriever):
        """The doc claims the ranking is C2, C1, C3 — a keyword win over the top vector hit."""
        results = retriever.retrieve("testing experience", "p1", [0.1, 0.2, 0.3])

        assert [r["id"] for r in results] == ["C2", "C1", "C3"]

    def test_worked_example_drops_chunk_below_min_score(self, retriever):
        """The doc claims C4 (0.150) is dropped by the default min_score of 0.3."""
        results = retriever.retrieve("testing experience", "p1", [0.1, 0.2, 0.3])

        assert "C4" not in [r["id"] for r in results]

    def test_top_hit_on_each_side_normalizes_to_one(self, retriever):
        """The doc claims max-normalization makes each side's best raw score exactly 1.0."""
        results = retriever.retrieve("testing experience", "p1", [0.1, 0.2, 0.3])
        by_id = {r["id"]: r for r in results}

        # C1 had the highest raw vector score, C2 the highest raw BM25 score.
        assert by_id["C1"]["vector_score"] == pytest.approx(1.0)
        assert by_id["C2"]["keyword_score"] == pytest.approx(1.0)

    def test_chunk_missing_from_one_side_scores_zero_there(self, retriever):
        """The doc claims a chunk absent from one candidate set contributes 0 on that side."""
        results = retriever.retrieve("testing experience", "p1", [0.1, 0.2, 0.3])
        by_id = {r["id"]: r for r in results}

        # C3 was never returned by BM25.
        assert by_id["C3"]["keyword_score"] == 0.0

    def test_min_score_cutoff_is_inclusive(self, retriever):
        """The doc claims the filter is `>=`, so a chunk scoring exactly min_score is kept."""
        results = retriever.retrieve("testing experience", "p1", [0.1, 0.2, 0.3], min_score=0.350)

        assert "C3" in [r["id"] for r in results]
