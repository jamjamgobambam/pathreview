"""LLM-based re-ranking of retrieved chunks."""

import json
import re
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
    max_tokens: int = 500


class Reranker:
    """Re-rank retrieved chunks by relevance to a query using an LLM.

    Sits downstream of HybridRetriever.retrieve(): the vector/keyword blend
    can be fooled by keyword repetition (see tests/unit/test_hybrid_keyword_bias.py),
    so this re-scores the candidate pool with an LLM before the caller takes
    the final top-k.
    """

    def __init__(self, config: RerankerConfig):
        """Initialize the reranker.

        Args:
            config: RerankerConfig with API settings
        """
        self.config = config
        self.client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)

    def rerank(self, query: str, chunks: list[dict], top_k: int | None = None) -> list[dict]:
        """Re-rank chunks by LLM-judged relevance to the query.

        Args:
            query: The original search query
            chunks: Candidate chunks (each a dict with at least "id", "text", "score")
            top_k: If given, truncate the reranked list to this many chunks

        Returns:
            Chunks reordered by relevance, each with an added "rerank_score" field.
            Falls back to the existing blended "score" order if the LLM call
            fails or its output can't be parsed.
        """
        if not chunks:
            return []

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a relevance-scoring assistant. "
                            "Respond only with a JSON object, no other text."
                        ),
                    },
                    {"role": "user", "content": self._build_prompt(query, chunks)},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            content = response.choices[0].message.content
        except Exception as e:
            logger.error("rerank_llm_call_failed", error=str(e), chunk_count=len(chunks))
            return self._fallback_order(chunks, top_k)

        scores = self._parse_scores(content)
        if not scores:
            logger.warning("rerank_parse_failed", raw_response=(content or "")[:200])
            return self._fallback_order(chunks, top_k)

        reranked = [
            {**chunk, "rerank_score": scores.get(str(chunk.get("id")), chunk.get("score", 0.0))}
            for chunk in chunks
        ]
        reranked.sort(key=lambda c: c["rerank_score"], reverse=True)

        logger.info(
            "rerank_complete",
            chunk_count=len(chunks),
            scored_count=len(scores),
            top_k=top_k,
        )

        return reranked[:top_k] if top_k is not None else reranked

    @staticmethod
    def _build_prompt(query: str, chunks: list[dict]) -> str:
        """Build the relevance-scoring prompt for a batch of candidate chunks."""
        lines = [
            f"Query: {query}",
            "",
            "Rate how relevant each numbered chunk below is to the query, "
            "on a scale from 0.0 (irrelevant) to 1.0 (highly relevant). "
            "Judge true topical relevance -- do not give a high score just "
            "because a chunk repeats a keyword from the query.",
            "Respond ONLY with a JSON object mapping chunk id to score, "
            'e.g. {"c1": 0.9, "c2": 0.1}.',
            "",
        ]
        for chunk in chunks:
            lines.append(f'[{chunk.get("id")}] {chunk.get("text", "")}')
        return "\n".join(lines)

    @staticmethod
    def _parse_scores(content: str | None) -> dict[str, float]:
        """Parse the LLM's JSON response into a chunk_id -> score mapping.

        Returns an empty dict (triggering the fallback order) if the response
        is missing, not valid JSON, or not a JSON object.
        """
        if not content:
            return {}

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        raw = json_match.group(0) if json_match else content

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}

        if not isinstance(data, dict):
            return {}

        scores: dict[str, float] = {}
        for chunk_id, value in data.items():
            try:
                scores[str(chunk_id)] = float(value)
            except (TypeError, ValueError):
                continue
        return scores

    @staticmethod
    def _fallback_order(chunks: list[dict], top_k: int | None) -> list[dict]:
        """Fall back to the existing blended-score order when re-ranking fails."""
        ordered = sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)
        return ordered[:top_k] if top_k is not None else ordered
