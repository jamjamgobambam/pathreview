"""LLM-based re-ranking of retrieved chunks (issue #34).

Second-stage pass over the hybrid-retrieved candidate set: prompts a smaller LLM
to score each chunk's relevance to the query, then reorders by that score. Opt-in
via HybridRetriever(enable_rerank=True); on any API or parse failure it falls back
to the original (blended-score) order so retrieval never breaks.
"""

import json
import re
from dataclasses import dataclass

import openai
import structlog

logger = structlog.get_logger()

# Cap the chunk text sent to the scoring LLM to bound input tokens as the
# candidate pool grows.
MAX_CHUNK_CHARS = 500


def _extract_json(content: str) -> object:
    """Load a JSON payload from LLM text, tolerating ```json code fences.

    Models often wrap JSON in a Markdown code fence; strip it before parsing so
    an otherwise-valid response isn't discarded.

    Args:
        content: Raw LLM response text

    Returns:
        The parsed JSON value.
    """
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    candidate = fenced.group(1) if fenced else content
    return json.loads(candidate)


@dataclass
class RerankConfig:
    """Configuration for LLM re-ranking."""

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 500


class LLMReranker:
    """Re-score and reorder retrieved chunks by LLM-judged relevance."""

    def __init__(self, config: RerankConfig):
        """Initialize the re-ranker.

        Args:
            config: RerankConfig with API settings
        """
        self.config = config
        self.client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)

    def rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        """Re-rank candidate chunks by LLM relevance to the query.

        Args:
            query: The user's text query
            chunks: Candidate chunk dicts (each with at least 'id' and 'text'),
                already ordered by blended score
            top_k: Number of chunks to return after re-ranking

        Returns:
            The top_k chunks ordered by LLM relevance, each with an added
            'rerank_score'. On empty input or any failure, falls back to the
            original order.
        """
        if not chunks:
            return []

        try:
            scores = self._score_chunks(query, chunks)
        except Exception as e:
            logger.warning("rerank_failed_fallback_to_blended", error=str(e))
            return chunks[:top_k]

        # A relevance score is required for every candidate. A partial response
        # would bury the unscored chunks (including ones the blend ranked highly),
        # so treat it as a failure and keep the blended order instead.
        if len(scores) < len(chunks):
            logger.warning(
                "rerank_incomplete_fallback_to_blended",
                scored=len(scores),
                candidates=len(chunks),
            )
            return chunks[:top_k]

        # Copy rather than mutate the caller's dicts. Python's sort is stable, so
        # ties preserve the incoming (blended) order.
        scored = [dict(chunk, rerank_score=scores[i]) for i, chunk in enumerate(chunks)]
        scored.sort(key=lambda c: c["rerank_score"], reverse=True)
        results = scored[:top_k]

        logger.info("rerank_complete", candidates=len(chunks), returned=len(results))
        return results

    def _score_chunks(self, query: str, chunks: list[dict]) -> dict[int, float]:
        """Ask the LLM to score each chunk 0-1 for relevance to the query.

        Args:
            query: The user's text query
            chunks: Candidate chunk dicts

        Returns:
            Mapping of chunk index -> relevance score (0.0-1.0). Missing or
            unparseable entries are omitted (treated as 0.0 by the caller).
        """
        numbered = "\n".join(
            f"[{i}] {chunk.get('text', '')[:MAX_CHUNK_CHARS]}" for i, chunk in enumerate(chunks)
        )
        prompt = (
            f"Query: {query}\n\n"
            f"Candidate chunks:\n{numbered}\n\n"
            "Score how well each chunk answers the query, from 0.0 (irrelevant) "
            "to 1.0 (directly answers it). Respond ONLY with a JSON array of "
            'objects like [{"index": 0, "score": 0.9}], one per chunk.'
        )

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "You are a precise relevance judge."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        content = response.choices[0].message.content
        if content is None:
            return {}

        scores = self._parse_scores(content)
        if not scores:
            logger.warning("rerank_no_scores_parsed", content_preview=content[:120])
        return scores

    @staticmethod
    def _parse_scores(content: str) -> dict[int, float]:
        """Parse the LLM's JSON response into an index->score map.

        Args:
            content: Raw LLM response text

        Returns:
            Mapping of index -> score for every well-formed entry; malformed
            entries are skipped rather than raising.
        """
        scores: dict[int, float] = {}
        parsed = _extract_json(content)
        if not isinstance(parsed, list):
            return scores
        for entry in parsed:
            try:
                idx = int(entry["index"])
                score = float(entry["score"])
            except (KeyError, TypeError, ValueError):
                continue
            scores[idx] = max(0.0, min(1.0, score))
        return scores
