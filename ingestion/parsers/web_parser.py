"""Parser for portfolio website HTML content."""

import re
from html import unescape

from .base import BaseParser, ParseResult


class WebParser(BaseParser):
    """Parse website HTML into readable portfolio text."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse website HTML content and extract useful portfolio text.

        Args:
            content: HTML string or bytes

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            ValueError: If content is not a valid string or bytes
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        title = self._extract_title(content)
        text = self._extract_text(content)
        stripped_text = self._normalize_text(text)
        word_count = len(stripped_text.split())

        metadata = {
            "source_type": "web",
            "title": title,
            "word_count": word_count,
        }

        return ParseResult(
            text=stripped_text,
            metadata=metadata,
            source_type="web",
        )

    def _extract_title(self, content: str) -> str:
        """Extract the first <title> element from HTML."""
        match = re.search(r"<title[^>]*>(.*?)</title>", content, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return ""
        return unescape(re.sub(r"\s+", " ", match.group(1))).strip()

    def _extract_text(self, content: str) -> str:
        """Extract visible text content from HTML while preserving meaningful sections."""
        content = re.sub(r"<head[\s\S]*?</head>", " ", content, flags=re.IGNORECASE)
        content = re.sub(r"<script[\s\S]*?</script>", " ", content, flags=re.IGNORECASE)
        content = re.sub(r"<style[\s\S]*?</style>", " ", content, flags=re.IGNORECASE)

        body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", content, flags=re.IGNORECASE)
        if body_match:
            content = body_match.group(1)

        text = re.sub(r"<[^>]+>", " ", content)
        text = unescape(text)
        return text

    def _normalize_text(self, content: str) -> str:
        """Normalize whitespace and remove filler noise from extracted text."""
        normalized = re.sub(r"\s+", " ", content)
        normalized = re.sub(r"\s+([,.!?;:])", r"\1", normalized)
        return normalized.strip()
