import httpx
import structlog
from bs4 import BeautifulSoup

from .base import BaseParser, ParseResult

logger = structlog.get_logger()

FETCH_TIMEOUT_SECONDS = 10.0


class WebPageParser(BaseParser):
    """Parser for arbitrary portfolio web pages, fetched over HTTP."""

    def fetch_and_parse(self, url: str) -> ParseResult:
        """
        Fetch a URL and parse its HTML into plain text.

        Args:
            url: The portfolio page URL to fetch

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            httpx.HTTPStatusError: If the page returns a non-2xx status
            httpx.HTTPError: On connection errors or timeouts
            ValueError: If the response is not HTML content
        """
        response = httpx.get(url, timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            raise ValueError(f"Unsupported content type for {url}: {content_type!r}")

        return self.parse(response.text, url=url)

    def parse(self, content: str | bytes, url: str = "") -> ParseResult:
        """
        Parse already-fetched HTML content.

        Args:
            content: HTML string or bytes
            url: The source URL, stored in metadata

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            ValueError: If content is not a valid string/bytes
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        soup = BeautifulSoup(content, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "noscript"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = soup.get_text(separator="\n", strip=True)
        word_count = len(text.split())

        metadata = {
            "source_type": "web",
            "url": url,
            "title": title,
            "word_count": word_count,
        }

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="web",
        )
