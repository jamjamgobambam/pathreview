"""LLM-based reranking of retrieved chunks."""

import json
import re

import openai
import structlog

from core.config import settings

logger = structlog.get_logger()

MAX_CHUNK_CHARS_IN_PROMPT = 500


class Reranker:
    """Re-scores retrieved chunks by LLM-judged relevance to the query."""

    def __init__(self, client: openai.OpenAI | None = None, model: str | None = None):
        """Initialize reranker.

        Args:
            client: OpenAI-compatible client. Built from settings if not given.
            model: Model name to use for scoring. Falls back to settings.reranker_model.
        """
        self.client = client or openai.OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        self.model = model or settings.reranker_model

    def rerank(self, query: str, chunks: list[dict], top_k: int | None = None) -> list[dict]:
        """Re-score chunks by relevance to query, using one batch LLM call.

        On success, each chunk's "score" is replaced with the LLM-judged
        relevance score and the list is re-sorted. On any failure (LLM call
        error, unparseable response, or missing scores), falls back to the
        chunks in their original order, since retrieve() already sorted them
        by blended vector/keyword score.

        Args:
            query: Original query text
            chunks: Chunks from HybridRetriever.retrieve(), already blended-sorted
            top_k: If given, truncate the returned list to this many chunks

        Returns:
            Re-scored (or, on failure, unmodified) list of chunk dicts
        """
        if not chunks:
            return chunks

        try:
            scores = self._score_batch(query, chunks)
        except Exception as e:
            logger.warning("reranker_failed_fallback_to_blended", error=str(e))
            return chunks[:top_k] if top_k else chunks

        reranked = []
        for chunk in chunks:
            chunk = dict(chunk)
            if chunk["id"] in scores:
                chunk["score"] = scores[chunk["id"]]
            reranked.append(chunk)

        reranked.sort(key=lambda c: c["score"], reverse=True)

        return reranked[:top_k] if top_k else reranked

    def _score_batch(self, query: str, chunks: list[dict]) -> dict[str, float]:
        """Score all chunks in one LLM call.

        Args:
            query: Original query text
            chunks: Chunks to score

        Returns:
            Mapping of chunk id to relevance score (0-1)

        Raises:
            ValueError: If the LLM response can't be parsed into scores
        """
        prompt = self._build_prompt(query, chunks)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a relevance scoring assistant. Score how well each "
                        "chunk answers the query, from 0.0 (irrelevant) to 1.0 "
                        "(directly answers it). Respond with only a JSON object "
                        'mapping each chunk id to its score, e.g. {"c1": 0.9, "c2": 0.1}.'
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=max(100, len(chunks) * 20),
        )

        content = response.choices[0].message.content
        return self._parse_scores(content)

    def _build_prompt(self, query: str, chunks: list[dict]) -> str:
        """Build the batch scoring prompt.

        Args:
            query: Original query text
            chunks: Chunks to score

        Returns:
            Prompt text listing the query and each chunk's id/text
        """
        lines = [f"Query: {query}", "", "Chunks:"]
        for chunk in chunks:
            text = chunk.get("text", "")[:MAX_CHUNK_CHARS_IN_PROMPT]
            lines.append(f'- id: "{chunk["id"]}", text: "{text}"')
        return "\n".join(lines)

    def _parse_scores(self, raw: str) -> dict[str, float]:
        """Parse the LLM's JSON score mapping from its raw response.

        Checks for a fenced ```json block first (matching the convention in
        rag/generator/output_parser.py), then falls back to raw JSON.

        Args:
            raw: Raw LLM response content

        Returns:
            Mapping of chunk id to score

        Raises:
            ValueError: If no valid JSON object could be parsed
        """
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
        json_str = json_match.group(1) if json_match else raw

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"could not parse reranker response as JSON: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("reranker response was not a JSON object")

        return {str(chunk_id): float(score) for chunk_id, score in data.items()}
