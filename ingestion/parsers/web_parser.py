import httpx
from bs4 import BeautifulSoup

from .base import BaseParser, ParseResult

# Tags whose contents are never portfolio copy (navigation, styling, scripts).
NOISE_TAGS = ["script", "style", "noscript", "nav", "footer"]

# Guardrails for fetching arbitrary user-supplied URLs.
FETCH_TIMEOUT_SECONDS = 10.0
MAX_PAGE_BYTES = 2_000_000  # 2 MB
USER_AGENT = "PathReview/0.1 (portfolio ingestion)"


class WebParser(BaseParser):
    """Parser for personal portfolio website pages."""

    def fetch(self, url: str) -> str:
        """
        Download a portfolio page and return its raw HTML.

        Args:
            url: The portfolio website URL (must be http or https).

        Returns:
            The page's raw HTML as a string.

        Raises:
            ValueError: If the URL scheme is invalid, the page is unreachable,
                returns an error status, is too large, or is not HTML.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError("Portfolio URL must start with http:// or https://")

        try:
            response = httpx.get(
                url,
                timeout=FETCH_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError(f"Failed to fetch portfolio URL: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type.lower():
            raise ValueError(
                f"Portfolio URL did not return an HTML page "
                f"(content-type: {content_type or 'unknown'})"
            )

        if len(response.content) > MAX_PAGE_BYTES:
            raise ValueError("Portfolio page is too large to ingest")

        html: str = response.text
        return html

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Extract readable text from a portfolio page's HTML.

        Args:
            content: Raw HTML markup (str or bytes).

        Returns:
            ParseResult with the visible text and page metadata.

        Raises:
            ValueError: If content is not str/bytes, or has no readable text.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        soup = BeautifulSoup(content, "html.parser")

        # Remove tags that never contain portfolio copy before extracting text.
        for tag in soup(NOISE_TAGS):
            tag.decompose()

        title = soup.title.get_text(strip=True) if soup.title else ""

        text = self._collapse_whitespace(soup.get_text(separator="\n"))
        if not text:
            raise ValueError("No readable text found on the portfolio page")

        metadata = {
            "source_type": "portfolio",
            "title": title,
            "word_count": len(text.split()),
        }

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="portfolio",
        )

    def _collapse_whitespace(self, text: str) -> str:
        """Trim each line and drop blank lines so the text is compact."""
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)
