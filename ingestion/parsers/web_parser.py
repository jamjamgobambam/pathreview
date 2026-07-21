"""Parser for portfolio website pages."""

from __future__ import annotations

import hashlib
from html import unescape
from html.parser import HTMLParser

import httpx

from .base import BaseParser, ParseResult


class _VisibleTextExtractor(HTMLParser):
    """Extract visible text from HTML while skipping script and style blocks."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0
        self._title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = unescape(data).strip()
        if not text:
            return

        if self._in_title:
            self._title_parts.append(text)
            return

        if self._skip_depth == 0:
            self._parts.append(text)

    @property
    def text(self) -> str:
        return " ".join(self._parts)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()


class WebParser(BaseParser):
    """Parser for portfolio website URLs."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Fetch and parse a portfolio website URL.

        Args:
            content: Portfolio URL string or bytes

        Returns:
            ParseResult with extracted text and page metadata

        Raises:
            ValueError: If content is invalid or not a supported URL
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        if not isinstance(content, str):
            raise ValueError("Content must be a string URL or bytes")

        url = content.strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("Content must be an http or https URL")

        response = httpx.get(url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()

        extractor = _VisibleTextExtractor()
        extractor.feed(response.text)

        page_text = extractor.text.strip()
        title = extractor.title or self._extract_title_fallback(response.text)
        content_hash = hashlib.sha256(page_text.encode("utf-8")).hexdigest()

        metadata = {
            "source_type": "web",
            "url": url,
            "title": title,
            "word_count": len(page_text.split()),
            "content_hash": content_hash,
        }

        return ParseResult(
            text=page_text,
            metadata=metadata,
            source_type="web",
        )

    @staticmethod
    def _extract_title_fallback(html_text: str) -> str:
        """Fallback title extraction when the parser does not capture it."""
        lower_html = html_text.lower()
        start_tag = lower_html.find("<title>")
        end_tag = lower_html.find("</title>")
        if start_tag == -1 or end_tag == -1 or end_tag <= start_tag:
            return ""

        start = start_tag + len("<title>")
        return unescape(html_text[start:end_tag]).strip()