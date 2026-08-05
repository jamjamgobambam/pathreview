import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import BaseParser, ParseResult

# Tags whose text is boilerplate/navigation rather than portfolio content.
_BOILERPLATE_TAGS = ("script", "style", "nav", "footer", "header", "aside", "noscript")

# Elements that typically hold the meaningful content of a portfolio page.
_CONTENT_SECTION_KEYWORDS = ("about", "bio", "project", "experience", "work", "skill")

_FETCH_TIMEOUT_SECONDS = 10.0
_MAX_CONTENT_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_REDIRECTS = 5
_USER_AGENT = "PathReviewBot/1.0 (+https://github.com/ascherj/pathreview)"


class WebParserError(ValueError):
    """Raised when a portfolio URL cannot be fetched or parsed."""


def _is_blocked_address(host: str) -> bool:
    """
    Return True if the host resolves to a non-public address.

    Blocks loopback, private, link-local, and other reserved ranges to guard
    against SSRF via user-supplied portfolio URLs.
    """
    try:
        addr_infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # Cannot resolve - treat as blocked (nothing safe to fetch).
        return True

    for info in addr_infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return True
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return True
    return False


def _validate_url(url: str) -> None:
    """
    Validate that a URL is safe to fetch.

    Raises:
        WebParserError: If the scheme is not http/https, the hostname is
            missing, or the host resolves to a non-public address.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise WebParserError(f"URL must use http or https scheme, got: {parsed.scheme!r}")
    if not parsed.hostname:
        raise WebParserError("URL must include a hostname")
    if _is_blocked_address(parsed.hostname):
        raise WebParserError("Refusing to fetch internal or non-public address")


def fetch_url(url: str, *, timeout: float = _FETCH_TIMEOUT_SECONDS) -> str:
    """
    Fetch the HTML content of a portfolio URL.

    Args:
        url: The portfolio URL to fetch (must be http/https).
        timeout: Request timeout in seconds.

    Returns:
        The raw HTML content as a string.

    Raises:
        WebParserError: If the URL is invalid, blocked (SSRF), unreachable,
            or does not return HTML content.
    """
    _validate_url(url)

    # Follow redirects manually so every hop is re-validated against the SSRF
    # guard. httpx's follow_redirects would otherwise skip the guard and allow a
    # public URL to redirect into an internal address.
    current_url = url
    try:
        for _ in range(_MAX_REDIRECTS + 1):
            response = httpx.get(
                current_url,
                timeout=timeout,
                follow_redirects=False,
                headers={"User-Agent": _USER_AGENT},
            )
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    break
                current_url = urljoin(current_url, location)
                _validate_url(current_url)
                continue
            response.raise_for_status()
            break
        else:
            raise WebParserError("Too many redirects")
    except httpx.HTTPError as exc:
        raise WebParserError(f"Failed to fetch URL: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise WebParserError(f"Expected HTML content, got: {content_type!r}")

    if len(response.content) > _MAX_CONTENT_BYTES:
        raise WebParserError("Page content exceeds maximum allowed size")

    return response.text


class WebParser(BaseParser):
    """Parser for portfolio website HTML content."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse raw HTML from a portfolio page into clean text.

        Args:
            content: Raw HTML as a string or bytes.

        Returns:
            ParseResult with extracted text and metadata.

        Raises:
            WebParserError: If content is empty or yields no extractable text.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise WebParserError("Content must be a string or bytes")

        if not content.strip():
            raise WebParserError("Content is empty")

        soup = BeautifulSoup(content, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else None

        # Remove boilerplate before extracting text.
        for tag in soup(_BOILERPLATE_TAGS):
            tag.decompose()

        link_count = len(soup.find_all("a"))
        extracted_sections = self._extract_sections(soup)

        text = self._normalize_whitespace(soup.get_text(separator="\n"))
        if not text:
            raise WebParserError("No extractable text found in page")

        word_count = len(text.split())

        metadata = {
            "source_type": "portfolio",
            "title": title,
            "word_count": word_count,
            "link_count": link_count,
            "extracted_sections": extracted_sections,
        }

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="portfolio",
        )

    def _extract_sections(self, soup: BeautifulSoup) -> list[str]:
        """Detect likely portfolio sections from headings and id/class hints."""
        detected: set[str] = set()

        for heading in soup.find_all(["h1", "h2", "h3"]):
            heading_text = heading.get_text(strip=True).lower()
            for keyword in _CONTENT_SECTION_KEYWORDS:
                if keyword in heading_text:
                    detected.add(keyword)

        for element in soup.find_all(attrs={"id": True}):
            identifier = element.get("id", "").lower()
            for keyword in _CONTENT_SECTION_KEYWORDS:
                if keyword in identifier:
                    detected.add(keyword)

        return sorted(detected)

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse excess whitespace and blank lines."""
        lines = [line.strip() for line in text.splitlines()]
        non_empty = [line for line in lines if line]
        collapsed = "\n".join(non_empty)
        return re.sub(r"\n{3,}", "\n\n", collapsed).strip()
