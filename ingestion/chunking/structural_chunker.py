import re

import tiktoken

from .base import BaseChunker, Chunk
from .semantic_chunker import SemanticChunker


class StructuralChunker(BaseChunker):
    """
    Chunk markdown on heading boundaries while preserving hierarchy.

    Splits on h1, h2, h3 headings, preserves heading context,
    and uses semantic sub-chunking for large sections. A document with no
    headings is chunked as a single headingless section; content that appears
    before the first heading becomes its own headingless chunk while the
    remaining headings are handled normally — in either case the content is
    chunked rather than being silently dropped.
    """

    SECTION_TOKEN_LIMIT = 800

    def __init__(self) -> None:
        """Initialize the chunker."""
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.semantic_chunker = SemanticChunker()

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """
        Chunk markdown on heading boundaries.

        Args:
            text: The markdown text to chunk
            metadata: Document metadata

        Returns:
            List of Chunk objects with heading_path in metadata
        """
        if not text or not text.strip():
            return []

        # Extract sections with heading hierarchy
        sections = self._extract_sections(text)

        chunks = []
        for section in sections:
            heading_path = " > ".join(section["path"])
            section_text = section["content"]

            # Check if section is too large for single chunk
            section_tokens = len(self.encoder.encode(section_text))

            if section_tokens > self.SECTION_TOKEN_LIMIT:
                # Sub-chunk using semantic chunker
                section_metadata = metadata.copy()
                section_metadata.update(
                    {
                        "heading_path": heading_path,
                        "heading_level": section["level"],
                    }
                )
                sub_chunks = self.semantic_chunker.chunk(section_text, section_metadata)
                chunks.extend(sub_chunks)
            else:
                # Single chunk for this section
                section_metadata = metadata.copy()
                section_metadata.update(
                    {
                        "heading_path": heading_path,
                        "heading_level": section["level"],
                        "chunk_index": len(chunks),
                        "char_start": 0,
                        "char_end": len(section_text),
                    }
                )
                chunks.append(Chunk(text=section_text, metadata=section_metadata))

        return chunks

    def _extract_sections(self, text: str) -> list[dict]:
        """
        Extract sections from markdown with heading hierarchy.

        A new section is emitted whenever a heading boundary is crossed and once
        more for whatever remains at the end of the document. Content that never
        sits under a heading — a document with no headings at all, or a preamble
        before the first heading — is emitted as a headingless section (empty
        path, level 0) so it is chunked rather than silently dropped (issue #149).

        Returns list of dicts with: content, path (breadcrumb), level
        """
        lines = text.split("\n")
        sections: list[dict] = []
        heading_stack: list[tuple[int, str]] = []  # Stack of (level, heading_text)
        current_section_lines: list[str] = []

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Save the section that just ended, including any content that
                # appeared before the first heading (headingless preamble).
                section = self._build_section(current_section_lines, heading_stack)
                if section is not None:
                    sections.append(section)
                current_section_lines = []

                # Process the new heading
                heading_level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Update heading stack based on level
                while heading_stack and heading_stack[-1][0] >= heading_level:
                    heading_stack.pop()

                heading_stack.append((heading_level, heading_text))

            else:
                # Always collect content; headingless docs are no longer dropped.
                current_section_lines.append(line)

        # Save the final section. Documents with no headings land here with an
        # empty heading_stack and are returned as a single headingless section.
        section = self._build_section(current_section_lines, heading_stack)
        if section is not None:
            sections.append(section)

        return sections

    @staticmethod
    def _build_section(lines: list[str], heading_stack: list[tuple[int, str]]) -> dict | None:
        """
        Build a section dict from accumulated lines, or None if empty.

        When heading_stack is empty (no heading has been seen yet) the section is
        emitted with an empty path and level 0 so heading-free content is chunked
        instead of silently dropped (issue #149).
        """
        content = "\n".join(lines).strip()
        if not content:
            return None
        return {
            "content": content,
            "path": [h[1] for h in heading_stack],
            "level": heading_stack[-1][0] if heading_stack else 0,
        }
