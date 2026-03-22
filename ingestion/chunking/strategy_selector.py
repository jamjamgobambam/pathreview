from .base import BaseChunker, Chunk
from .semantic_chunker import SemanticChunker
from .structural_chunker import StructuralChunker


class StrategySelector:
    """Select and apply appropriate chunking strategy based on document type."""

    def __init__(self):
        """Initialize chunkers."""
        self.semantic_chunker = SemanticChunker()
        self.structural_chunker = StructuralChunker()

    def select_chunker(self, source_type: str) -> BaseChunker:
        """
        Select appropriate chunker based on document type.

        Args:
            source_type: One of "resume", "readme", "repo", or default

        Returns:
            Appropriate BaseChunker instance
        """
        if source_type == "resume":
            return self.semantic_chunker
        elif source_type == "readme":
            return self.structural_chunker
        elif source_type == "repo":
            return self.semantic_chunker
        else:
            # Default to semantic chunking
            return self.semantic_chunker

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """
        Chunk text using strategy selected by source_type.

        Args:
            text: The text to chunk
            metadata: Document metadata (must include source_type)

        Returns:
            List of chunks
        """
        source_type = metadata.get("source_type", "unknown")
        chunker = self.select_chunker(source_type)
        return chunker.chunk(text, metadata)
