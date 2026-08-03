"""LLM-based re-ranking of retrieved chunks (issue #34).

The hybrid retriever orders candidate chunks by a blended vector + keyword
score. That score is a lexical/embedding proxy for relevance and does not
judge whether a chunk actually answers the specific query. This module adds an
optional step that asks an LLM to score each candidate for relevance so the
most relevant chunks are surfaced before generation.
"""

import re
from typing import Any

import structlog

logger = structlog.get_logger()

RERANK_PROMPT = """You are scoring how relevant a document chunk is to a query.

Query:
{query}

Document chunk:
{chunk}

Respond with ONLY a number from 0.0 (irrelevant) to 1.0 (directly relevant).
No words, just the number."""


class LLMReranker:
    """Re-rank candidate chunks by LLM-judged relevance to the query."""

    def __init__(self, client: Any, model: str, temperature: float = 0.0):
        """Initialize the re-ranker.

        Args:
            client: An ``openai.OpenAI``-style client (injected for testability).
            model: Model identifier used for scoring.
            temperature: Sampling temperature; defaults to 0.0 for determinism.
        """
        self.client = client
        self.model = model
        self.temperature = temperature

    @classmethod
    def from_settings(cls, settings: Any, client: Any = None) -> "LLMReranker":
        """Build a reranker from application settings.

        Constructs an OpenRouter/OpenAI client from ``settings`` when one is
        not supplied, mirroring how ``ReviewGenerator`` builds its client.

        Args:
            settings: Settings object exposing ``openrouter_api_key``,
                ``openrouter_base_url``, and ``rerank_model``.
            client: Optional pre-built OpenAI-style client (injected in tests).

        Returns:
            A configured ``LLMReranker``.
        """
        if client is None:
            import openai

            client = openai.OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
            )
        return cls(client=client, model=settings.rerank_model)

    def rerank(self, query: str, chunks: list[dict], top_k: int = 10) -> list[dict]:
        """Score each chunk with the LLM and return the top_k, best first.

        Scoring is per-chunk and fault-tolerant: if the LLM call for a single
        chunk fails, that chunk falls back to its existing hybrid ``score``
        instead of discarding the successfully scored chunks. If every chunk
        fails, the original hybrid ordering is therefore preserved.

        Args:
            query: The user query.
            chunks: Candidate chunk dicts from the hybrid retriever.
            top_k: Maximum number of chunks to return.

        Returns:
            Re-ordered chunk dicts (length <= top_k). Each returned chunk gains
            a ``rerank_score`` field; the original ``score`` is preserved.
        """
        if not chunks:
            return []

        scored = [(self._safe_score(query, c), i, c) for i, c in enumerate(chunks)]
        # Sort by score descending; ties keep original hybrid order (stable).
        scored.sort(key=lambda t: (-t[0], t[1]))
        reranked = [dict(chunk, rerank_score=score) for score, _, chunk in scored]

        logger.info("rerank_complete", candidates=len(chunks), returned=min(top_k, len(chunks)))
        return reranked[:top_k]

    def _safe_score(self, query: str, chunk: dict) -> float:
        """Score a single chunk, falling back to its hybrid score on failure.

        Args:
            query: The user query.
            chunk: A single candidate chunk dict.

        Returns:
            The LLM relevance score, or the chunk's existing hybrid ``score``
            (default 0.0) if the LLM call fails.
        """
        try:
            return self._score_chunk(query, chunk)
        except Exception as e:
            fallback = float(chunk.get("score", 0.0))
            logger.warning("rerank_chunk_scoring_failed", error=str(e), fallback=fallback)
            return fallback

    def _score_chunk(self, query: str, chunk: dict) -> float:
        """Ask the LLM for a single relevance score in ``[0, 1]``.

        Args:
            query: The user query.
            chunk: A single candidate chunk dict.

        Returns:
            A relevance score between 0.0 and 1.0.
        """
        prompt = RERANK_PROMPT.format(query=query, chunk=chunk.get("text", ""))
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise relevance scorer."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=8,
        )
        return self._parse_score(response.choices[0].message.content)

    @staticmethod
    def _parse_score(content: str) -> float:
        """Extract the first number from LLM output and clamp to ``[0, 1]``.

        Args:
            content: Raw LLM response text.

        Returns:
            A parsed score in ``[0, 1]``; 0.0 when no number is found.
        """
        match = re.search(r"\d*\.?\d+", content or "")
        if not match:
            return 0.0
        return max(0.0, min(1.0, float(match.group())))
