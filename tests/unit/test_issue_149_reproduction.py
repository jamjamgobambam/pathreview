"""Regression tests for issue #149.

https://github.com/ascherj/pathreview/issues/149
StructuralChunker silently dropped documents that contain no headings.

`StructuralChunker._extract_sections()` used to only collect content lines
after a heading had been seen, and only save the final section when the
heading stack was non-empty. A document with zero markdown headings
therefore yielded zero sections, so `chunk()` returned an empty list and the
document was silently excluded from the RAG index.

The fix collects content lines regardless of whether a heading has been
seen yet, emitting a level-0 section (empty heading path) for text with no
enclosing heading. These tests guard against regressing that behavior.
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

        assert (
            "Important preamble" in combined
        ), "Issue #149 (related): content before the first heading is lost"
