"""LLM-based re-ranking of retrieved chunks (issue #34).

After hybrid retrieval blends vector and keyword scores, the ordering can
still surface keyword-heavy but off-topic chunks. This module adds an
optional secondary pass where a small, fast LLM scores each chunk's
relevance to the query so the most relevant chunks reach the generator.

The reranker is defensive by design: any LLM or parsing failure falls back
to the chunk's existing hybrid score, so a flaky model never makes results
worse than plain hybrid ranking.
"""

import re
from dataclasses import dataclass

import openai
import structlog

logger = structlog.get_logger()

# Matches the first (optionally signed / decimal) number in an LLM response,
# e.g. "8", "8.5", "score: 7". Used to parse the relevance score robustly.
_SCORE_PATTERN = re.compile(r"[-+]?\d*\.?\d+")

_SYSTEM_PROMPT = (
    "You are a relevance judge for a retrieval system. Given a user query and "
    "a document chunk, rate how relevant the chunk is to answering the query "
    "on a scale from 0 to 10, where 0 is completely irrelevant and 10 is "
    "highly relevant. Respond with only the number."
)


@dataclass
class RerankConfig:
    """Configuration for LLM re-ranking.

    Mirrors ReviewConfig but defaults to a low temperature and small token
    budget, since scoring should be deterministic and cheap.
    """

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 10


class LLMReranker:
    """Re-rank retrieved chunks by LLM-judged relevance to the query."""

    def __init__(self, config: RerankConfig):
        """Initialize the reranker.

        Args:
            config: RerankConfig with API settings.
        """
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    def rerank(self, query: str, chunks: list[dict], top_k: int | None = None) -> list[dict]:
        """Re-sort chunks by LLM relevance and return the top_k.

        Each returned chunk gains a ``rerank_score`` field (0.0-1.0). Chunks
        that cannot be scored by the LLM fall back to their existing hybrid
        ``score`` so ordering degrades gracefully rather than breaking.

        Args:
            query: The user query.
            chunks: Retrieved chunks (each a dict with at least ``text``).
            top_k: Maximum chunks to return. ``None`` returns all of them.

        Returns:
            Chunks sorted by ``rerank_score`` descending, truncated to top_k.
        """
        if not query or not chunks:
            logger.info(
                "rerank_empty_input",
                has_query=bool(query),
                chunk_count=len(chunks),
            )
            return []

        scored = []
        llm_failures = 0
        for chunk in chunks:
            rerank_score, failed = self._score_chunk(query, chunk)
            llm_failures += int(failed)
            scored.append({**chunk, "rerank_score": rerank_score})

        scored.sort(key=lambda c: c["rerank_score"], reverse=True)

        final = scored if top_k is None else scored[:top_k]

        logger.info(
            "rerank_complete",
            query_len=len(query),
            input_count=len(chunks),
            returned_count=len(final),
            llm_failures=llm_failures,
        )
        return final

    def _score_chunk(self, query: str, chunk: dict) -> tuple[float, bool]:
        """Score a single chunk's relevance via the LLM.

        Args:
            query: The user query.
            chunk: A single chunk dict.

        Returns:
            A ``(score, failed)`` tuple. ``score`` is 0.0-1.0; ``failed`` is
            True when the LLM call or parsing failed and the chunk's existing
            hybrid ``score`` was used as a fallback.
        """
        text = chunk.get("text", "")
        fallback = float(chunk.get("score", 0.0))

        if not text:
            return fallback, False

        prompt = f"Query: {query}\n\nChunk: {text}\n\nRelevance (0-10):"
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            content = response.choices[0].message.content
        except Exception as e:
            # API failure / rate limit: fall back to hybrid score (PLAN risk).
            logger.warning("rerank_llm_call_failed", error=str(e))
            return fallback, True

        parsed = self._parse_score(content)
        if parsed is None:
            logger.warning("rerank_unparseable_score", raw_output=content)
            return fallback, True

        return parsed, False

    @staticmethod
    def _parse_score(content: str | None) -> float | None:
        """Parse a 0-10 LLM response into a normalized 0.0-1.0 score.

        Args:
            content: Raw LLM output (may be None or contain extra text).

        Returns:
            Normalized score in [0.0, 1.0], or None if no number was found.
        """
        if not content:
            return None

        match = _SCORE_PATTERN.search(content)
        if match is None:
            return None

        value = float(match.group())
        # Clamp to the documented 0-10 range before normalizing.
        value = max(0.0, min(10.0, value))
        return value / 10.0
