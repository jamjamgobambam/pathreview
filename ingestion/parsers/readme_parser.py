import re

from .base import BaseParser, ParseResult


class ReadmeParser(BaseParser):
    """Parser for README markdown documents."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse a README from markdown content.

        Args:
            content: Markdown string or bytes

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            ValueError: If content is not a valid string/bytes
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        heading_hierarchy = self._extract_heading_hierarchy(content)
        heading_count = len(heading_hierarchy)
        word_count = len(content.split())
        has_code_blocks = bool(re.search(r"```", content))
        has_badges = bool(re.search(r"!\[.*?\]\(.*?\)", content))

        metadata = {
            "source_type": "readme",
            "heading_count": heading_count,
            "word_count": word_count,
            "has_code_blocks": has_code_blocks,
            "has_badges": has_badges,
        }

        return ParseResult(
            text=content,
            metadata=metadata,
            source_type="readme",
        )

    def _extract_heading_hierarchy(self, content: str) -> list[dict]:
        """
        Extract heading hierarchy from markdown.

        Returns a list of dicts with: level, text, line_number
        """
        headings = []
        for line_num, line in enumerate(content.split("\n")):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text,
                    "line": line_num,
                })
        return headings
