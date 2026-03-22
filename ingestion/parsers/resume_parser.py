import re
from io import BytesIO

from pypdf import PdfReader

from .base import BaseParser, ParseResult


SECTION_HEADERS = {
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "languages",
    "publications",
    "awards",
    "summary",
    "objective",
    "technical skills",
    "professional experience",
    "work experience",
}


class ResumeParser(BaseParser):
    """Parser for resume documents in PDF and Markdown formats."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse a resume from PDF or Markdown content.

        Args:
            content: PDF bytes or markdown string

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            ValueError: If content is neither PDF nor markdown
        """
        if isinstance(content, bytes):
            return self._parse_pdf(content)
        elif isinstance(content, str):
            return self._parse_markdown(content)
        else:
            raise ValueError("Content must be bytes (PDF) or str (Markdown)")

    def _parse_pdf(self, pdf_bytes: bytes) -> ParseResult:
        """Extract text from all pages of a PDF resume."""
        try:
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            page_count = len(pdf_reader.pages)

            # Extract text from all pages
            text_pages = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text_pages.append(page_text)

            full_text = "\n".join(text_pages)

            detected_sections = self._detect_sections(full_text)

            metadata = {
                "source_type": "resume",
                "page_count": page_count,
                "detected_sections": detected_sections,
            }

            return ParseResult(
                text=full_text,
                metadata=metadata,
                source_type="resume",
            )
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    def _parse_markdown(self, content: str) -> ParseResult:
        """Extract text from markdown resume, stripping markdown syntax."""
        # Remove markdown syntax
        text = self._strip_markdown(content)

        detected_sections = self._detect_sections(text)

        metadata = {
            "source_type": "resume",
            "page_count": 1,
            "detected_sections": detected_sections,
        }

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="resume",
        )

    def _strip_markdown(self, content: str) -> str:
        """Remove markdown syntax from content."""
        # Remove markdown headers
        text = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)

        # Remove markdown links [text](url)
        text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"\1", text)

        # Remove markdown bold **text** or __text__
        text = re.sub(r"[*_]{2}([^*_]+)[*_]{2}", r"\1", text)

        # Remove markdown italic *text* or _text_
        text = re.sub(r"[*_]([^*_]+)[*_]", r"\1", text)

        # Remove markdown code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)

        # Remove inline code
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove extra whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _detect_sections(self, text: str) -> list[str]:
        """Detect common resume sections from text."""
        detected = []
        text_lower = text.lower()

        for section in SECTION_HEADERS:
            # Look for section header patterns
            patterns = [
                rf"^{re.escape(section)}\s*$",
                rf"^{re.escape(section)}\s*[:|-]",
                rf"\n{re.escape(section)}\s*$",
                rf"\n{re.escape(section)}\s*[:|-]",
            ]

            for pattern in patterns:
                if re.search(pattern, text_lower, re.MULTILINE):
                    detected.append(section.title())
                    break

        return list(set(detected))  # Remove duplicates
