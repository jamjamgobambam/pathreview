"""Reproduction tests for issue #149.

https://github.com/ascherj/pathreview/issues/149
StructuralChunker silently drops documents that contain no headings.

`StructuralChunker._extract_sections()` only collects content lines after a
heading has been seen, and only saves the final section when the heading
stack is non-empty. A document with zero markdown headings therefore yields
zero sections, so `chunk()` returns an empty list and the document is
silently excluded from the RAG index.

These tests FAIL on the current code and are expected to pass once the fix
(fallback chunking for heading-less documents) lands in Week 9.
"""

import pytest

from ingestion.chunking.strategy_selector import StrategySelector
from ingestion.chunking.structural_chunker import StructuralChunker


@pytest.mark.unit
class TestIssue149Reproduction:
    """Documents without headings must not be silently dropped."""

    @pytest.fixture
    def chunker(self):
        return StructuralChunker()

    def test_plain_text_document_is_not_dropped(self, chunker):
        """A non-empty document with no headings must produce >= 1 chunk."""
        text = (
            "PathReview is a tool for reviewing code submissions.\n\n"
            "It uses RAG to ground feedback in course materials.\n\n"
            "Install the dependencies and run the dev server to get started."
        )
        result = chunker.chunk(text, {"source": "readme"})

        # FAILS on current code: result == []
        assert len(result) >= 1, (
            "Issue #149: heading-less document was silently dropped "
            "(chunk() returned an empty list)"
        )

    def test_readme_without_headings_survives_ingestion_path(self):
        """The real ingestion path: source_type='readme' routes to
        StructuralChunker, so a heading-less README vanishes from the index."""
        selector = StrategySelector()
        text = "A README written as plain paragraphs, without any # headings."
        result = selector.chunk(text, {"source_type": "readme"})

        # FAILS on current code: result == []
        assert len(result) >= 1, (
            "Issue #149: README with no headings produced zero chunks via "
            "the readme ingestion path"
        )

    def test_content_before_first_heading_is_not_lost(self):
        """Preamble text that appears before the first heading is also
        discarded by _extract_sections(); it should be preserved."""
        chunker = StructuralChunker()
        text = (
            "Important preamble that describes the project.\n\n"
            "# First Heading\n"
            "Section content.\n"
        )
        result = chunker.chunk(text, {"source": "readme"})
        combined = " ".join(c.text for c in result)

        # FAILS on current code: the preamble never appears in any chunk
        assert "Important preamble" in combined, (
            "Issue #149 (related): content before the first heading is lost"
        )
