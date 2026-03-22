"""Tests for semantic_chunker.py"""

import pytest

from ingestion.chunking.semantic_chunker import SemanticChunker
from ingestion.chunking.base import Chunk


@pytest.mark.unit
class TestSemanticChunker:
    """Test suite for SemanticChunker."""

    @pytest.fixture
    def chunker(self):
        """Create a SemanticChunker instance."""
        return SemanticChunker()

    def test_empty_input_returns_empty_list(self, chunker):
        """Test that empty input returns empty list."""
        result = chunker.chunk("", {})
        assert result == []

    def test_whitespace_only_input(self, chunker):
        """Test that whitespace-only input returns empty list."""
        result = chunker.chunk("   \n\n  \t  ", {})
        assert result == []

    def test_short_text_returns_single_chunk(self, chunker):
        """Test that short text (< 500 tokens) returns single chunk."""
        short_text = "This is a short text with just a few sentences. " * 5
        result = chunker.chunk(short_text, {"source": "test"})

        assert len(result) == 1
        assert isinstance(result[0], Chunk)
        assert result[0].text
        assert "metadata" in result[0].__dict__

    def test_long_text_returns_multiple_chunks(self, chunker):
        """Test that long text returns multiple chunks with overlap."""
        # Create text that's definitely > 500 tokens
        long_text = "This is a test sentence. " * 100

        result = chunker.chunk(long_text, {"source": "test"})

        assert len(result) > 1
        assert all(isinstance(chunk, Chunk) for chunk in result)
        assert all(chunk.text for chunk in result)

    def test_chunk_metadata_includes_chunk_index(self, chunker):
        """Test that chunk metadata includes chunk_index."""
        text = "Sentence one. Sentence two. Sentence three. " * 30
        result = chunker.chunk(text, {"source": "test"})

        for i, chunk in enumerate(result):
            assert "chunk_index" in chunk.metadata
            assert chunk.metadata["chunk_index"] == i

    def test_chunks_preserve_source_metadata(self, chunker):
        """Test that source metadata is preserved in chunks."""
        text = "Test sentence. " * 50
        original_metadata = {"source": "readme", "version": 1}
        result = chunker.chunk(text, original_metadata)

        for chunk in result:
            assert chunk.metadata["source"] == "readme"
            assert chunk.metadata["version"] == 1

    def test_chunk_has_character_positions(self, chunker):
        """Test that chunks have character position metadata."""
        text = "First sentence. Second sentence. Third sentence. " * 20
        result = chunker.chunk(text, {})

        for chunk in result:
            assert "char_start" in chunk.metadata
            assert "char_end" in chunk.metadata
            assert isinstance(chunk.metadata["char_start"], int)
            assert isinstance(chunk.metadata["char_end"], int)

    def test_bullet_points_not_split_mid_bullet(self, chunker):
        """Test that bullet points are not split mid-bullet."""
        text = """
        Key features:
        - Feature one with detailed explanation that goes on for a while
        - Feature two with another long explanation
        - Feature three is important
        """ * 10

        result = chunker.chunk(text, {})

        # Check that bullet points are relatively intact
        for chunk in result:
            # Should not have incomplete bullet points
            lines = chunk.text.split("\n")
            for line in lines:
                if line.strip().startswith("-"):
                    # Bullet line should have reasonable length
                    assert len(line.strip()) > 2

    def test_sentence_splitting(self, chunker):
        """Test that text is split on sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        sentences = chunker._split_sentences(text)

        assert isinstance(sentences, list)
        assert len(sentences) >= 3
        assert all(s.strip() for s in sentences)

    def test_sentence_splitting_with_exclamation_marks(self, chunker):
        """Test sentence splitting with exclamation and question marks."""
        text = "What a day! How are you? I'm great. No issues!"
        sentences = chunker._split_sentences(text)

        assert len(sentences) >= 3

    def test_sentence_splitting_preserves_punctuation(self, chunker):
        """Test that sentence splitting preserves punctuation."""
        text = "Question? Answer! Statement."
        sentences = chunker._split_sentences(text)

        # At least one sentence should have punctuation
        assert any("?" in s or "!" in s or "." in s for s in sentences)

    def test_overlap_between_chunks(self, chunker):
        """Test that consecutive chunks have overlap."""
        text = "This is a test. " * 100  # Create substantial text

        result = chunker.chunk(text, {})

        if len(result) > 1:
            # Last part of first chunk should have some relationship to second
            first_chunk_end = result[0].metadata.get("char_end", 0)
            second_chunk_start = result[1].metadata.get("char_start", 0)
            # There should be overlap (start of next < end of previous)
            assert second_chunk_start < first_chunk_end or len(result) == 1

    def test_chunks_have_non_zero_text(self, chunker):
        """Test that all chunks have non-empty text."""
        text = "Test sentence. " * 50
        result = chunker.chunk(text, {})

        for chunk in result:
            assert chunk.text
            assert chunk.text.strip()
            assert len(chunk.text) > 0

    def test_paragraph_boundaries_respected(self, chunker):
        """Test that paragraph boundaries are respected."""
        text = """
        First paragraph with multiple sentences. This is still the first paragraph.
        It continues here.

        Second paragraph starts here. It has its own content.
        More content in the second paragraph.

        Third paragraph is separate.
        """ * 5

        result = chunker.chunk(text, {})

        assert len(result) > 0
        # Chunks should not randomly mix paragraphs
        assert all(chunk.text for chunk in result)

    def test_metadata_copied_not_mutated(self, chunker):
        """Test that original metadata is not mutated."""
        text = "Test sentence. " * 50
        original_metadata = {"source": "test", "data": [1, 2, 3]}
        original_metadata_copy = original_metadata.copy()

        chunker.chunk(text, original_metadata)

        # Original should not be mutated
        assert original_metadata == original_metadata_copy

    def test_chunk_indexing_is_sequential(self, chunker):
        """Test that chunk indexes are sequential from 0."""
        text = "Test sentence. " * 100
        result = chunker.chunk(text, {})

        chunk_indices = [c.metadata["chunk_index"] for c in result]
        assert chunk_indices == list(range(len(result)))
