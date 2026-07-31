import re
from html.parser import HTMLParser

import httpx
import structlog

from .base import BaseParser, ParseResult

logger = structlog.get_logger()


SKIP_TAGS = {"script", "style", "noscript", "head", "nav", "footer"}
BLOCK_TAGS = {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6"}


class _HTMLTextExtractor(HTMLParser):
    """Extracts readable text from HTML, skipping script/style/nav boilerplate."""

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        text = "".join(self._parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


class WebParser(BaseParser):
    """Parser for portfolio website pages."""

    TIMEOUT_SECONDS = 10.0

    def fetch(self, url: str) -> str:
        """
        Fetch a portfolio page's HTML content.

        Args:
            url: The portfolio URL to fetch

        Returns:
            Raw HTML content as a string

        Raises:
            ValueError: If the page can't be fetched or isn't an HTML page
        """
        try:
            response = httpx.get(url, timeout=self.TIMEOUT_SECONDS, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch {url}: {str(e)}") from e

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            raise ValueError(f"Unsupported content type for {url}: {content_type or 'unknown'}")

        return response.text

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse a portfolio page from HTML content.

        Args:
            content: HTML string or bytes

        Returns:
            ParseResult with extracted readable text and metadata

        Raises:
            ValueError: If content is neither str nor bytes
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be bytes or str (HTML)")

        try:
            extractor = _HTMLTextExtractor()
            extractor.feed(content)
            text = extractor.get_text()
        except Exception as e:
            raise ValueError(f"Failed to parse HTML: {str(e)}") from e

        title = self._extract_title(content)
        word_count = len(text.split())

        metadata = {
            "source_type": "web",
            "title": title,
            "word_count": word_count,
        }

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="web",
        )

    def _extract_title(self, content: str) -> str | None:
        """Extract the page <title>, if present."""
        match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None
