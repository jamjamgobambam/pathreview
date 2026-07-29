"""LLM-based re-ranker for retrieved chunks."""

import re
from typing import Any

import structlog

logger = structlog.get_logger()


class LLMReranker:
    """Re-ranks retrieved chunks by prompting an LLM to score relevance."""

    def __init__(self, client: Any, model: str) -> None:
        self.client = client
        self.model = model

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score each chunk's relevance to query and return sorted descending.

        Args:
            query: The user's search query.
            chunks: List of dicts each with at least 'id', 'text', and 'score'.

        Returns:
            Same chunks with 'rerank_score' added, sorted by rerank_score desc.
        """
        if not chunks:
            return []

        results = []
        for chunk in chunks:
            score = self._score_chunk(query, chunk)
            results.append({**chunk, "rerank_score": score})

        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        return results

    def _score_chunk(self, query: str, chunk: dict) -> float:
        """Ask the LLM to rate relevance of a single chunk (0.0–1.0)."""
        prompt = (
            f"Rate how relevant the following text is to the query on a scale from "
            f"0.0 (not relevant) to 1.0 (highly relevant). "
            f"Respond with only a single float number.\n\n"
            f"Query: {query}\n\nText: {chunk.get('text', '')}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content or ""
            return self._parse_score(raw, fallback=chunk.get("score", 0.0))
        except Exception:
            logger.warning("reranker_llm_call_failed", chunk_id=chunk.get("id"))
            return float(chunk.get("score", 0.0))

    @staticmethod
    def _parse_score(text: str, fallback: float = 0.0) -> float:
        """Extract a float in [0, 1] from LLM response; clamp and fall back."""
        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            logger.warning("reranker_unparseable_response", raw=text)
            return float(fallback)
        try:
            value = float(match.group())
            return max(0.0, min(1.0, value))
        except ValueError:
            return float(fallback)
