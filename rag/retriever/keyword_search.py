"""BM25-based keyword search retriever."""

import structlog
from rank_bm25 import BM25Okapi

logger = structlog.get_logger()

# Stripped only from token edges, so terms like "c++", "c#", and "node.js"
# stay intact while sentence-trailing punctuation ("React.", "Python,") doesn't
# prevent a token from matching the same word elsewhere.
_PUNCTUATION_STRIP_CHARS = ".,;:!?\"'()[]{}"


class KeywordSearcher:
    """BM25-based keyword retrieval for sparse search."""

    def __init__(self) -> None:
        """Initialize keyword searcher."""
        self.bm25 = None
        self.chunks: list[dict] = []

    def index(self, chunks: list[dict]) -> None:
        """Build BM25 index from chunks.

        Args:
            chunks: List of chunk dicts with 'text' field
        """
        self.chunks = chunks
        tokenized_corpus = [self._tokenize(chunk["text"]) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info("keyword_index_built", chunk_count=len(chunks))

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search chunks by keyword relevance using BM25.

        Args:
            query: Search query string
            top_k: Number of top results to return

        Returns:
            List of chunks sorted by BM25 score (descending)
        """
        if not self.bm25 or not self.chunks:
            logger.warning("keyword_search_empty_index")
            return []

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # Create list of (chunk, score) tuples
        scored_chunks = [(self.chunks[i], scores[i]) for i in range(len(self.chunks))]

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Take top_k and enrich with scores
        results = []
        for chunk, score in scored_chunks[:top_k]:
            result = dict(chunk)
            result["bm25_score"] = float(score)
            results.append(result)

        logger.info(
            "keyword_search_complete", query_len=len(query_tokens), results_count=len(results)
        )
        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text: lowercase, split on whitespace, and strip
        leading/trailing punctuation from each token.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        raw_tokens = text.lower().split()
        stripped = (t.strip(_PUNCTUATION_STRIP_CHARS) for t in raw_tokens)
        return [t for t in stripped if t]
