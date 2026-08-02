import re
from html.parser import HTMLParser

import httpx
import structlog

from .base import BaseParser, ParseResult

logger = structlog.get_logger()

_SKIP_TAGS = {"script", "style", "noscript", "head"}


class _HTMLTextExtractor(HTMLParser):
    """Strips tags/scripts/styles from HTML, keeping visible text and the page title."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._chunks.append(stripped)

    def get_text(self) -> str:
        text = "\n".join(self._chunks)
        return re.sub(r"\n{3,}", "\n\n", text).strip()


class WebParser(BaseParser):
    """Parser for portfolio website URLs: fetches the page and extracts visible text."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Fetch a portfolio URL and extract its visible text.

        Args:
            content: The portfolio URL to fetch (str)

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            ValueError: If content is not a non-empty URL string, the URL is
                unreachable, returns a non-2xx status, or the response isn't HTML.
        """
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content must be a non-empty URL string")

        url = content.strip()

        try:
            response = httpx.get(url, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"Portfolio URL returned status {e.response.status_code}: {url}"
            ) from e
        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch portfolio URL {url}: {e}") from e

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            raise ValueError(
                f"Portfolio URL did not return HTML content (got '{content_type}'): {url}"
            )

        extractor = _HTMLTextExtractor()
        extractor.feed(response.text)
        text = extractor.get_text()
        word_count = len(text.split())

        metadata = {
            "source_type": "portfolio",
            "url": url,
            "title": extractor.title.strip(),
            "word_count": word_count,
        }

        logger.info(
            "portfolio_parsed",
            url=url,
            word_count=word_count,
            text_preview=text[:200],
        )

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="portfolio",
        )
