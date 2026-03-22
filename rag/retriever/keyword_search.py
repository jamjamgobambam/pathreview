"""BM25-based keyword search retriever."""

from rank_bm25 import BM25Okapi
import structlog

logger = structlog.get_logger()


class KeywordSearcher:
    """BM25-based keyword retrieval for sparse search."""

    def __init__(self):
        """Initialize keyword searcher."""
        self.bm25 = None
        self.chunks = []

    def index(self, chunks: list[dict]) -> None:
        """Build BM25 index from chunks.

        Args:
            chunks: List of chunk dicts with 'text' field
        """
        self.chunks = chunks
        tokenized_corpus = [
            self._tokenize(chunk["text"]) for chunk in chunks
        ]
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
        scored_chunks = [
            (self.chunks[i], scores[i]) for i in range(len(self.chunks))
        ]

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Take top_k and enrich with scores
        results = []
        for chunk, score in scored_chunks[:top_k]:
            result = dict(chunk)
            result["bm25_score"] = float(score)
            results.append(result)

        logger.info("keyword_search_complete", query_len=len(query_tokens),
                   results_count=len(results))
        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple tokenization: lowercase and split on whitespace.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        return text.lower().split()
