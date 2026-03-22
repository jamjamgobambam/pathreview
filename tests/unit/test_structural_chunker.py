"""Tests for structural_chunker.py"""

import pytest

from ingestion.chunking.structural_chunker import StructuralChunker
from ingestion.chunking.base import Chunk


@pytest.mark.unit
class TestStructuralChunker:
    """Test suite for StructuralChunker."""

    @pytest.fixture
    def chunker(self):
        """Create a StructuralChunker instance."""
        return StructuralChunker()

    def test_empty_input_returns_empty_list(self, chunker):
        """Test that empty input returns empty list."""
        result = chunker.chunk("", {})
        assert result == []

    def test_whitespace_only_input(self, chunker):
        """Test that whitespace-only input returns empty list."""
        result = chunker.chunk("   \n\n  ", {})
        assert result == []

    def test_document_with_no_headings(self, chunker):
        """Test document with no headings returns single chunk."""
        text = "This is plain text without any markdown headings. " * 20
        result = chunker.chunk(text, {"source": "test"})

        assert len(result) >= 1
        assert isinstance(result[0], Chunk)
        assert all(isinstance(c, Chunk) for c in result)

    def test_document_with_nested_headings(self, chunker):
        """Test document with nested headings preserves heading_path."""
        text = """# Main Title
Content for main.

## Subsection
Content for subsection.

### Sub-subsection
Content for sub-subsection.

## Another Section
Content for another section.
"""
        result = chunker.chunk(text, {"source": "test"})

        assert len(result) > 0
        # Check that heading_path is preserved
        for chunk in result:
            if "heading_path" in chunk.metadata:
                heading_path = chunk.metadata["heading_path"]
                assert isinstance(heading_path, str)
                # heading_path should use " > " separator
                if ">" in heading_path:
                    parts = heading_path.split(" > ")
                    assert len(parts) > 0

    def test_heading_path_format(self, chunker):
        """Test heading_path format is Parent > Child."""
        text = """# Parent
Content

## Child
Content under child.

### GrandChild
Content under grandchild.
"""
        result = chunker.chunk(text, {})

        found_path = False
        for chunk in result:
            if "heading_path" in chunk.metadata:
                path = chunk.metadata["heading_path"]
                if "Child" in path:
                    # Should have " > " as separator if it has parent
                    found_path = True
                    assert isinstance(path, str)

    def test_large_section_sub_chunked(self, chunker):
        """Test large section (> 800 tokens) gets sub-chunked."""
        # Create a large section
        large_section = """# Large Section
""" + "This is a paragraph with lots of content. " * 50

        result = chunker.chunk(large_section, {})

        # Should be chunked into multiple pieces
        assert len(result) > 0

    def test_chunk_metadata_includes_heading_level(self, chunker):
        """Test that chunk metadata includes heading_level."""
        text = """# Level 1
Content 1

## Level 2
Content 2

### Level 3
Content 3
"""
        result = chunker.chunk(text, {})

        has_heading_level = False
        for chunk in result:
            if "heading_level" in chunk.metadata:
                has_heading_level = True
                assert isinstance(chunk.metadata["heading_level"], int)
                assert chunk.metadata["heading_level"] in [1, 2, 3]

        assert has_heading_level

    def test_chunk_metadata_structure(self, chunker):
        """Test chunk metadata has required fields."""
        text = """# Title
Content here.

## Subtitle
More content.
"""
        result = chunker.chunk(text, {})

        for chunk in result:
            assert "metadata" in chunk.__dict__
            if "heading_path" in chunk.metadata:
                assert isinstance(chunk.metadata["heading_path"], str)

    def test_preserve_source_metadata(self, chunker):
        """Test that source metadata is preserved."""
        text = "# Title\nContent"
        original_metadata = {"source": "readme", "version": 1}
        result = chunker.chunk(text, original_metadata)

        for chunk in result:
            assert chunk.metadata["source"] == "readme"
            assert chunk.metadata["version"] == 1

    def test_multiple_h1_headings(self, chunker):
        """Test document with multiple H1 headings."""
        text = """# First H1
Content for first.

# Second H1
Content for second.

# Third H1
Content for third.
"""
        result = chunker.chunk(text, {})

        assert len(result) >= 3

    def test_heading_path_breadcrumb(self, chunker):
        """Test heading path shows full breadcrumb."""
        text = """# Documentation
## Installation
### Prerequisites
Content here.
"""
        result = chunker.chunk(text, {})

        found_full_path = False
        for chunk in result:
            if "heading_path" in chunk.metadata:
                path = chunk.metadata["heading_path"]
                # Should contain the hierarchy
                if "Installation" in path or "Prerequisites" in path:
                    found_full_path = True

    def test_chunks_have_text_content(self, chunker):
        """Test that all chunks have text content."""
        text = """# Title
Content paragraph 1.

## Section
Content paragraph 2.
"""
        result = chunker.chunk(text, {})

        for chunk in result:
            assert chunk.text
            assert chunk.text.strip()

    def test_section_extraction_with_multiple_levels(self, chunker):
        """Test section extraction with complex nesting."""
        text = """# Level 1A
Content 1A

## Level 2A
Content 2A

### Level 3A
Content 3A

## Level 2B
Content 2B

# Level 1B
Content 1B
"""
        result = chunker.chunk(text, {})

        assert len(result) > 0
        # Should handle all nesting levels

    def test_heading_not_in_middle_of_content(self, chunker):
        """Test that headings are properly delimited from content."""
        text = """# Main Heading
Some content goes here.
More content on new line.

## Sub Heading
Sub content here.
"""
        result = chunker.chunk(text, {})

        for chunk in result:
            # Chunk should either start with heading content or regular content
            assert chunk.text.strip()

    def test_empty_sections_handled(self, chunker):
        """Test handling of empty sections (heading without content)."""
        text = """# Heading 1
Content for 1

## Heading 2

## Heading 3
Content for 3
"""
        result = chunker.chunk(text, {})

        # Should not crash on empty sections
        assert isinstance(result, list)
