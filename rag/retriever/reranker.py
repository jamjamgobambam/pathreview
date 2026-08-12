"""LLM-based re-ranking of retrieved chunks."""

from dataclasses import dataclass

import openai
import structlog

logger = structlog.get_logger()


@dataclass
class RerankerConfig:
    """Configuration for LLM-based re-ranking."""

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 10


class LLMReranker:
    """Re-ranks retrieved chunks by prompting an LLM to score relevance.

    Runs as an optional post-processing step after HybridRetriever.retrieve().
    If the LLM call fails or returns something unparseable for a chunk, that
    chunk falls back to its existing blended score rather than crashing the
    request or being unfairly dropped to the bottom.
    """

    def __init__(self, config: RerankerConfig):
        """Initialize reranker.

        Args:
            config: RerankerConfig with API settings
        """
        self.config = config
        self.client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)

    def rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        """Re-rank chunks by LLM-scored relevance to the query.

        Args:
            query: The original text query
            chunks: Candidate chunks (already filtered/blended by hybrid retrieval)
            top_k: Number of chunks to return after re-ranking

        Returns:
            Top top_k chunks, sorted by llm_score descending. Each returned
            chunk dict is a shallow copy of the input with an added
            "llm_score" key.
        """
        if not chunks:
            return []

        scored_chunks = []
        for chunk in chunks:
            llm_score = self._score_chunk(query, chunk)
            scored = dict(chunk)
            scored["llm_score"] = llm_score
            scored_chunks.append(scored)

        scored_chunks.sort(key=lambda c: c["llm_score"], reverse=True)

        logger.info(
            "rerank_complete",
            query_len=len(query),
            input_count=len(chunks),
            output_count=min(top_k, len(scored_chunks)),
        )

        return scored_chunks[:top_k]

    def _score_chunk(self, query: str, chunk: dict) -> float:
        """Score a single chunk's relevance to the query via LLM call.

        Args:
            query: The original text query
            chunk: A single retrieved chunk dict

        Returns:
            Relevance score in [0, 1]. Falls back to the chunk's existing
            blended "score" (or 0.0) if the LLM call fails or its output
            can't be parsed as a float in range.
        """
        fallback_score = float(chunk.get("score", 0.0))
        text = chunk.get("text", "")

        prompt = (
            "Rate how relevant the following passage is to the query, "
            "on a scale from 0.0 (irrelevant) to 1.0 (highly relevant). "
            "Respond with only the number, no other text.\n\n"
            f"Query: {query}\n\n"
            f"Passage: {text}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a precise relevance-scoring assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            raw = response.choices[0].message.content.strip()
            score = float(raw)

            if not (0.0 <= score <= 1.0):
                logger.warning("rerank_score_out_of_range", raw=raw)
                return fallback_score

            return score

        except (ValueError, TypeError) as e:
            logger.warning("rerank_score_unparseable", error=str(e))
            return fallback_score
        except Exception as e:
            logger.error("rerank_llm_call_failed", error=str(e))
            return fallback_score
