from dataclasses import dataclass


@dataclass
class ParseResult:
    """Result of parsing a source document."""
    text: str
    metadata: dict
    source_type: str


class BaseParser:
    """Abstract base class for all content parsers."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse content and return a ParseResult.

        Args:
            content: The content to parse (str or bytes depending on parser)

        Returns:
            ParseResult with extracted text, metadata, and source_type

        Raises:
            NotImplementedError: Subclasses must implement this method
            ValueError: If content format is invalid
        """
        raise NotImplementedError("Subclasses must implement parse()")
