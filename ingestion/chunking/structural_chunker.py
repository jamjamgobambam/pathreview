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
                section_metadata.update({
                    "heading_path": heading_path,
                    "heading_level": section["level"],
                })
                sub_chunks = self.semantic_chunker.chunk(section_text, section_metadata)
                chunks.extend(sub_chunks)
            else:
                # Single chunk for this section
                section_metadata = metadata.copy()
                section_metadata.update({
                    "heading_path": heading_path,
                    "heading_level": section["level"],
                    "chunk_index": len(chunks),
                    "char_start": 0,
                    "char_end": len(section_text),
                })
                chunks.append(Chunk(text=section_text, metadata=section_metadata))

        return chunks

    def _extract_sections(self, text: str) -> list[dict]:
        """
        Extract sections from markdown with heading hierarchy.

        Returns list of dicts with: content, path (breadcrumb), level
        """
        lines = text.split("\n")
        sections = []
        heading_stack = []  # Stack of (level, heading_text)
        current_section_lines = []
        current_level = 0

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Save previous section if exists
                if current_section_lines:
                    if heading_stack:
                        sections.append({
                            "content": "\n".join(current_section_lines).strip(),
                            "path": [h[1] for h in heading_stack],
                            "level": heading_stack[-1][0] if heading_stack else 0,
                        })
                    current_section_lines = []

                # Process new heading
                heading_level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # Update heading stack based on level
                while heading_stack and heading_stack[-1][0] >= heading_level:
                    heading_stack.pop()

                heading_stack.append((heading_level, heading_text))
                current_level = heading_level

            else:
                # Regular content line
                if heading_stack or current_section_lines:  # Only collect if we have a heading
                    current_section_lines.append(line)

        # Save final section
        if current_section_lines and heading_stack:
            sections.append({
                "content": "\n".join(current_section_lines).strip(),
                "path": [h[1] for h in heading_stack],
                "level": heading_stack[-1][0] if heading_stack else 0,
            })

        return sections
