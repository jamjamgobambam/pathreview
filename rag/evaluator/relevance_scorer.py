"""Score retrieval relevance."""

import structlog

logger = structlog.get_logger()


class RelevanceScorer:
    """Score relevance of retrieved chunks to query."""

    def score(self, query: str, chunks: list[dict]) -> float:
        """Score retrieval relevance.

        Args:
            query: Query text
            chunks: Retrieved chunks

        Returns:
            Relevance score 0.0-1.0
        """
        if not chunks:
            logger.info("relevance_score_empty_chunks")
            return 0.0

        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return 0.0

        relevances = []

        for chunk in chunks:
            text = chunk.get("text", "")
            chunk_tokens = set(self._tokenize(text))

            if not chunk_tokens:
                relevances.append(0.0)
                continue

            # Keyword overlap as relevance signal
            overlap = len(query_tokens & chunk_tokens)
            recall = overlap / len(query_tokens)
            precision = overlap / len(chunk_tokens)
            relevance = (recall + precision) / 2
            relevances.append(relevance)

        # Return average relevance
        avg_relevance = sum(relevances) / len(relevances)

        logger.info(
            "relevance_scored",
            query_len=len(query_tokens),
            chunks_count=len(chunks),
            avg_score=avg_relevance,
        )

        return min(avg_relevance, 1.0)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        tokens = []
        for token in text.lower().split():
            normalized = token.strip(".,!?;:()[]{}")
            if len(normalized) > 3 and normalized.endswith("s"):
                normalized = normalized[:-1]
            if normalized:
                tokens.append(normalized)
        return tokens
