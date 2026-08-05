import re

import tiktoken

from .base import BaseChunker, Chunk
from .semantic_chunker import SemanticChunker


class StructuralChunker(BaseChunker):
    """
    Chunk markdown on heading boundaries while preserving hierarchy.

    Splits on h1, h2, h3 headings, preserves heading context,
    and uses semantic sub-chunking for large sections.
    """

    SECTION_TOKEN_LIMIT = 800

    def __init__(self):
        """Initialize the chunker."""
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.semantic_chunker = SemanticChunker()

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """
        Chunk markdown on heading boundaries.

        Documents (or leading preamble) with no heading above them are
        still chunked, as a section with an empty heading path, instead
        of being silently dropped.

        Args:
            text: The markdown text to chunk
            metadata: Document metadata

        Returns:
            List of Chunk objects. Chunks that fall under a heading carry
            heading_path/heading_level in metadata; chunks with no heading
            above them (an entire headingless document, or a document's
            preamble) do not.
        """
        if not text or not text.strip():
            return []

        # Extract sections with heading hierarchy
        sections = self._extract_sections(text)

        chunks = []
        for section in sections:
            section_text = section["content"]

            section_metadata = metadata.copy()
            if section["path"]:
                section_metadata.update(
                    {
                        "heading_path": " > ".join(section["path"]),
                        "heading_level": section["level"],
                    }
                )

            # Check if section is too large for single chunk
            section_tokens = len(self.encoder.encode(section_text))

            if section_tokens > self.SECTION_TOKEN_LIMIT:
                # Sub-chunk using semantic chunker
                sub_chunks = self.semantic_chunker.chunk(section_text, section_metadata)
                chunks.extend(sub_chunks)
            else:
                # Single chunk for this section
                section_metadata.update(
                    {
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

        Content above the first heading (or all content, if the document
        has no headings at all) is captured as its own section with an
        empty path rather than being dropped.

        Returns list of dicts with: content, path (breadcrumb), level
        """
        lines = text.split("\n")
        sections = []
        heading_stack = []  # Stack of (level, heading_text)
        current_section_lines = []

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Save previous section if it has content — this may be a
                # normal section under a heading, or preamble collected
                # before the first heading was seen
                content = "\n".join(current_section_lines).strip()
                if content:
                    sections.append(
                        {
                            "content": content,
                            "path": [h[1] for h in heading_stack],
                            "level": heading_stack[-1][0] if heading_stack else 0,
                        }
                    )
                current_section_lines = []

                # Process new heading
                heading_level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Update heading stack based on level
                while heading_stack and heading_stack[-1][0] >= heading_level:
                    heading_stack.pop()

                heading_stack.append((heading_level, heading_text))

            else:
                # Regular content line — always collect, even before the
                # first heading is seen or when the document has no
                # headings at all
                current_section_lines.append(line)

        # Save final section (may have no heading if the document had none)
        content = "\n".join(current_section_lines).strip()
        if content:
            sections.append(
                {
                    "content": content,
                    "path": [h[1] for h in heading_stack],
                    "level": heading_stack[-1][0] if heading_stack else 0,
                }
            )

        return sections
