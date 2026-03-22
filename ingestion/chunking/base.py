from dataclasses import dataclass


@dataclass
class Chunk:
    """A single chunk of text with metadata."""
    text: str
    metadata: dict


class BaseChunker:
    """Abstract base class for text chunking strategies."""

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """
        Chunk text according to strategy.

        Args:
            text: The text to chunk
            metadata: Document metadata (includes source_id, heading_path if applicable)

        Returns:
            List of Chunk objects with preserved metadata

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError("Subclasses must implement chunk()")
