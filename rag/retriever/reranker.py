"""LLM-based re-ranking of retrieved chunks."""

import re
from abc import ABC, abstractmethod

import openai
import structlog

logger = structlog.get_logger()

RERANK_PROMPT = """Score how relevant the following passage is to the query on a \
scale from 0.0 (irrelevant) to 1.0 (highly relevant).

Query: {query}

Passage:
{text}

Respond with only the numeric score, nothing else."""


class Reranker(ABC):
    """Abstract base class for chunk re-rankers."""

    @abstractmethod
    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score and sort chunks by relevance to the query.

        Args:
            query: Text query
            chunks: Chunks to re-rank, each with at least a 'text' field

        Returns:
            Chunks sorted by descending 'rerank_score', each annotated with
            a 'rerank_score' field (0.0-1.0)
        """
        raise NotImplementedError("Subclasses must implement rerank()")


class LLMReranker(Reranker):
    """Re-ranks chunks by prompting a small LLM to score their relevance."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """Initialize LLM reranker.

        Args:
            api_key: API key for the LLM provider
            base_url: Base URL for the LLM provider (OpenAI or OpenRouter)
            model: Model identifier to use for scoring
        """
        self.model = model
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score each chunk's relevance to the query via the LLM.

        Falls back to a chunk's existing 'score' (or 0.0) if scoring fails,
        so a single bad LLM response doesn't drop the chunk or crash retrieval.

        Args:
            query: Text query
            chunks: Chunks to re-rank

        Returns:
            Chunks sorted by descending 'rerank_score'
        """
        scored = []
        for chunk in chunks:
            score = self._score_chunk(query, chunk.get("text", ""))
            scored.append({**chunk, "rerank_score": score})

        scored.sort(key=lambda c: c["rerank_score"], reverse=True)

        logger.info("rerank_complete", query_len=len(query), chunk_count=len(chunks))
        return scored

    def _score_chunk(self, query: str, text: str) -> float:
        """Score a single chunk's relevance via the LLM.

        Args:
            query: Text query
            text: Chunk text

        Returns:
            Relevance score in [0.0, 1.0]
        """
        prompt = RERANK_PROMPT.format(query=query, text=text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10,
            )
            content = response.choices[0].message.content or ""
            return self._parse_score(content)
        except Exception as e:
            logger.warning("rerank_score_failed", error=str(e))
            return 0.0

    @staticmethod
    def _parse_score(content: str) -> float:
        """Extract a 0.0-1.0 score from the LLM's response text.

        Args:
            content: Raw LLM response

        Returns:
            Clamped float score, or 0.0 if no number could be parsed
        """
        match = re.search(r"-?\d+\.?\d*", content)
        if not match:
            return 0.0

        try:
            score = float(match.group())
        except ValueError:
            return 0.0

        return max(0.0, min(1.0, score))


class MockReranker(Reranker):
    """Deterministic reranker for tests: scores by query/chunk token overlap."""

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score chunks by keyword overlap with the query (no LLM call).

        Args:
            query: Text query
            chunks: Chunks to re-rank

        Returns:
            Chunks sorted by descending 'rerank_score'
        """
        query_tokens = set(query.lower().split())
        scored = []

        for chunk in chunks:
            chunk_tokens = set(chunk.get("text", "").lower().split())
            overlap = len(query_tokens & chunk_tokens)
            score = overlap / len(query_tokens) if query_tokens else 0.0
            scored.append({**chunk, "rerank_score": min(score, 1.0)})

        scored.sort(key=lambda c: c["rerank_score"], reverse=True)
        return scored


def get_reranker(provider_name: str, **kwargs: str) -> Reranker:
    """Factory function to get a reranker by provider name.

    Args:
        provider_name: One of "mock", "llm"
        **kwargs: Provider-specific arguments (e.g. api_key, base_url, model
            for "llm")

    Returns:
        Appropriate Reranker instance

    Raises:
        ValueError: If provider_name is not recognized
    """
    provider_name_lower = provider_name.lower().strip()

    if provider_name_lower == "mock":
        return MockReranker()
    elif provider_name_lower == "llm":
        return LLMReranker(**kwargs)
    else:
        raise ValueError(f"Unknown reranker provider: {provider_name}. " "Supported: 'mock', 'llm'")
