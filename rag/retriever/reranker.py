"""LLM-based re-ranker for retrieved chunks."""

import json
import re
from typing import Any

import openai
import structlog

from core.config import settings

logger = structlog.get_logger()


def build_reranker() -> "LLMReranker | None":
    """Return a Groq-backed LLMReranker, or None if GROQ_API_KEY is not set.

    Uses the openai SDK pointed at Groq's OpenAI-compatible endpoint so no
    extra dependency is needed beyond what pathreview already requires.
    """
    if not settings.groq_api_key:
        logger.info("reranker_disabled_no_groq_key")
        return None

    client = openai.OpenAI(
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
    )
    return LLMReranker(client=client, model=settings.groq_model)


class LLMReranker:
    """Re-ranks retrieved chunks by prompting an LLM to score relevance."""

    def __init__(self, client: Any, model: str) -> None:
        self.client = client
        self.model = model

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score all chunks in one LLM call and return sorted descending.

        Args:
            query: The user's search query.
            chunks: List of dicts each with at least 'id', 'text', and 'score'.

        Returns:
            Same chunks with 'rerank_score' added, sorted by rerank_score desc.
        """
        if not chunks:
            return []

        scores = self._score_chunks(query, chunks)
        results = [
            {**chunk, "rerank_score": score} for chunk, score in zip(chunks, scores, strict=False)
        ]
        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        return results

    def _score_chunks(self, query: str, chunks: list[dict]) -> list[float]:
        """Score all chunks in a single LLM call for efficiency and comparative context.

        Args:
            query: The user's search query.
            chunks: Chunks to score.

        Returns:
            List of floats in [0, 1], one per chunk, in the same order as input.
        """
        numbered = "\n\n".join(
            f"{i + 1}. {chunk.get('text', '')}" for i, chunk in enumerate(chunks)
        )
        prompt = (
            f"Score how relevant each numbered chunk is to the query from "
            f"0.0 (not relevant) to 1.0 (highly relevant). "
            f"Respond with only a JSON array of floats in order. "
            f"Example for 3 chunks: [0.8, 0.3, 0.95]\n\n"
            f"Query: {query}\n\nChunks:\n{numbered}"
        )
        fallbacks = [float(chunk.get("score", 0.0)) for chunk in chunks]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            raw = response.choices[0].message.content or ""
            return self._parse_scores(raw, fallbacks)
        except Exception as exc:
            logger.warning("reranker_llm_call_failed", error=str(exc))
            return fallbacks

    @staticmethod
    def _parse_scores(text: str, fallbacks: list[float]) -> list[float]:
        """Extract [0,1] floats from a JSON array; use fallback per entry if out of range.

        Args:
            text: Raw LLM response expected to contain a JSON array.
            fallbacks: Per-chunk fallback scores used when a value is missing or out of range.

        Returns:
            List of floats, one per chunk.
        """
        match = re.search(r"\[([^\]]*)\]", text)
        if not match:
            logger.warning("reranker_unparseable_response", raw=text)
            return list(fallbacks)
        try:
            values = json.loads(f"[{match.group(1)}]")
            if len(values) != len(fallbacks):
                logger.warning(
                    "reranker_wrong_score_count",
                    expected=len(fallbacks),
                    got=len(values),
                )
                return list(fallbacks)
            result = []
            for v, fb in zip(values, fallbacks, strict=False):
                try:
                    fv = float(v)
                    result.append(fv if 0.0 <= fv <= 1.0 else fb)
                except (ValueError, TypeError):
                    result.append(fb)
            return result
        except (ValueError, json.JSONDecodeError):
            logger.warning("reranker_unparseable_response", raw=text)
            return list(fallbacks)
