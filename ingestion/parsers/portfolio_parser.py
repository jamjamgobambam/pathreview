import re

import requests

from .base import BaseParser, ParseResult


class PortfolioParser(BaseParser):
    """Parser for portfolio websites."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Fetch and extract readable text from a portfolio website.
        """

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        if not isinstance(content, str):
            raise ValueError("Portfolio content must be a URL string")

        try:
            response = requests.get(content, timeout=10)
            response.raise_for_status()

            html = response.text

            # Remove scripts and styles
            html = re.sub(
                r"<script.*?>.*?</script>",
                "",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )

            html = re.sub(
                r"<style.*?>.*?</style>",
                "",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )

            # Strip remaining HTML tags
            extracted_text = re.sub(r"<[^>]+>", " ", html)

            # Normalize whitespace
            extracted_text = re.sub(r"\s+", " ", extracted_text).strip()

            metadata = {
                "source_type": "portfolio",
                "url": content,
                "character_count": len(extracted_text),
            }

            return ParseResult(
                text=extracted_text,
                metadata=metadata,
                source_type="portfolio",
            )

        except requests.RequestException as exc:
            raise ValueError(f"Failed to fetch portfolio website: {str(exc)}") from exc
