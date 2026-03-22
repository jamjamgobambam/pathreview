import re

import tiktoken

from .base import BaseChunker, Chunk


class SemanticChunker(BaseChunker):
    """
    Chunk text on sentence boundaries while maintaining target token size.

    Uses sentence boundaries rather than naive period splitting,
    handles bullet points, and targets ~500 token chunks with 50 token overlap.
    """

    TARGET_CHUNK_TOKENS = 500
    OVERLAP_TOKENS = 50
    MAX_TOKENS = 800

    def __init__(self):
        """Initialize the chunker with tiktoken encoder."""
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """
        Chunk text on sentence boundaries.

        Args:
            text: The text to chunk
            metadata: Document metadata

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # Split into sentences
        sentences = self._split_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0
        overlap_buffer = []
        overlap_tokens = 0
        char_start = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = len(self.encoder.encode(sentence))

            # If adding this sentence would exceed our target, save current chunk
            if current_tokens + sentence_tokens > self.TARGET_CHUNK_TOKENS and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": len(chunks),
                    "char_start": char_start,
                    "char_end": char_start + len(chunk_text),
                })
                chunks.append(Chunk(text=chunk_text, metadata=chunk_metadata))

                # Move to next chunk with overlap
                char_start += len(chunk_text)
                current_chunk = overlap_buffer.copy()
                current_tokens = overlap_tokens

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

            # Maintain overlap buffer
            if current_tokens > self.TARGET_CHUNK_TOKENS:
                overlap_buffer = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                overlap_tokens = sum(
                    len(self.encoder.encode(s)) for s in overlap_buffer
                )

        # Add final chunk if not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": len(chunks),
                "char_start": char_start,
                "char_end": char_start + len(chunk_text),
            })
            chunks.append(Chunk(text=chunk_text, metadata=chunk_metadata))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences on boundaries.

        Handles:
        - Periods followed by spaces
        - Exclamation marks
        - Question marks
        - Newlines (for bullet points)
        - Preserves the punctuation
        """
        # Replace multiple newlines with markers
        text = re.sub(r"\n{2,}", "\n", text)

        # Split on sentence boundaries
        sentence_pattern = r"(?<=[.!?])\s+(?=[A-Z])|(?<=\n)(?=[-•*])|(?<=\n)(?=[A-Z])"
        raw_sentences = re.split(sentence_pattern, text)

        sentences = []
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

        return sentences
