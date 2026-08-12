import re
from html.parser import HTMLParser

from .base import BaseParser, ParseResult


class _TextExtractor(HTMLParser):
    """Extract visible text and page-title content from HTML."""

    _SKIPPED_TAGS = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """Track skipped elements and title content."""
        tag = tag.lower()

        if tag in self._SKIPPED_TAGS:
            self._skip_depth += 1
        elif tag == "title" and self._skip_depth == 0:
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        """Stop tracking skipped elements and title content."""
        tag = tag.lower()

        if tag in self._SKIPPED_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        """Collect visible text outside skipped elements."""
        if self._skip_depth > 0:
            return

        if self._in_title:
            self.title_parts.append(data)
            return

        self.parts.append(data)


class WebParser(BaseParser):
    """Parse visible text from portfolio website HTML."""

    @staticmethod
    def _close_unterminated_skipped_tags(content: str) -> str:
        """Remove unterminated skipped tags so later text can still be parsed."""
        skipped_tags = ("script", "style", "noscript", "template")

        for tag in skipped_tags:
            pattern = rf"<{tag}\b[^>]*>(?!.*</{tag}\s*>)"
            content = re.sub(
                pattern,
                "",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )

        return content

    def parse(self, content: str | bytes) -> ParseResult:
        """Extract readable text and metadata from HTML content.

        Args:
            content: Portfolio page HTML as text or UTF-8 bytes.

        Returns:
            Parsed page text and metadata.

        Raises:
            ValueError: If the supplied content cannot be parsed as HTML text.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        if not isinstance(content, str):
            raise ValueError("Content must be an HTML string or bytes")

        # sanitize malformed skipped tags before parsing
        content = self._close_unterminated_skipped_tags(content)

        extractor = _TextExtractor()
        extractor.feed(content)
        extractor.close()

        text = self._normalize_whitespace(extractor.parts)
        title = self._normalize_whitespace(extractor.title_parts)

        return ParseResult(
            text=text,
            metadata={
                "title": title,
                "word_count": len(text.split()),
            },
            source_type="web",
        )

    @staticmethod
    def _normalize_whitespace(parts: list[str]) -> str:
        """Join text fragments and collapse repeated whitespace."""
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
