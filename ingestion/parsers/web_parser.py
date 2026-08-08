import httpx
import structlog
from bs4 import BeautifulSoup

from .base import BaseParser, ParseResult

logger = structlog.get_logger()


class WebParser(BaseParser):
    """Parser for extracting text from a portfolio website URL."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Fetch and parse HTML content from a URL.

        Args:
            content: The URL string to fetch.

        Returns:
            ParseResult with extracted text and metadata.

        Raises:
            ValueError: If the URL is invalid, not a string, or fetch fails.
        """
        if not isinstance(content, str):
            raise ValueError("WebParser expects a URL string as content")

        url = content

        if not url.startswith("http"):
            raise ValueError(f"Invalid URL: {url}")

        try:
            # Fetch the webpage
            logger.info("Fetching portfolio website", url=url)
            # Add a generic user agent to prevent basic blocks
            headers = {"User-Agent": "Mozilla/5.0 (compatible; PathReviewBot/1.0)"}
            response = httpx.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
            html_content = response.text

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script, style, nav, and footer elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "meta"]):
                element.decompose()

            # Extract text
            text = soup.get_text(separator="\n", strip=True)

            if not text:
                logger.warning("No text extracted from URL", url=url)

            metadata = {
                "source_url": url,
                "word_count": len(text.split()),
                "title": soup.title.string.strip() if soup.title and soup.title.string else None,
            }

            return ParseResult(text=text, metadata=metadata, source_type="portfolio")

        except httpx.RequestError as e:
            logger.error("Failed to fetch URL", url=url, error=str(e))
            raise ValueError(f"Failed to fetch portfolio URL: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error fetching URL", url=url, error=str(e))
            raise ValueError(f"HTTP error fetching portfolio URL: {e.response.status_code}") from e
        except Exception as e:
            logger.error("Error parsing portfolio URL", url=url, error=str(e))
            raise ValueError(f"Error parsing portfolio URL: {e}") from e
