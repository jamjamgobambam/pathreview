"""LLM-based re-ranking of retrieved chunks.

The hybrid retriever orders candidates purely by a mechanical blend of
vector similarity and BM25 keyword scores -- no semantic judgment. This
module adds an optional pass that asks a (smaller/cheaper) LLM to score how
relevant each candidate chunk actually is to the query, then reorders by
that judgment before the retriever truncates to top-k.

Design contract (kept deliberately safe so it can be dropped into the
retrieval path without changing behavior unless explicitly configured):

* Any LLM error, timeout, or malformed output -> the original ranking is
  returned untouched. Re-ranking can only help ordering, never break it.
* Chunks the LLM does not score keep their original blended ``score`` for
  ordering. Scores for ids that aren't in the candidate pool are ignored.
* Pools larger than ``batch_size`` are split across multiple LLM calls
  rather than silently truncated.
"""

import json
import re
from dataclasses import dataclass

import openai
import structlog

logger = structlog.get_logger()


RERANK_SYSTEM_PROMPT = (
    "You are a precise search-relevance judge. "
    "You reply with a single JSON object and nothing else."
)


@dataclass
class RerankerConfig:
    """Configuration for the LLM re-ranker.

    Mirrors ``rag.generator.review_generator.ReviewConfig`` so the same
    OpenAI-compatible settings (e.g. OpenRouter) can be reused. Defaults
    favor a cheap, deterministic scoring pass: ``temperature=0.0`` and a
    small ``max_tokens`` budget.
    """

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 512
    batch_size: int = 20


class LLMReranker:
    """Re-score and reorder retrieved chunks by LLM-judged relevance."""

    def __init__(self, config: RerankerConfig, client: openai.OpenAI | None = None):
        """Initialize the re-ranker.

        Args:
            config: RerankerConfig with API settings and batch size.
            client: Optional pre-built OpenAI-compatible client. Injecting
                one keeps the class unit-testable without network access;
                when omitted, a client is constructed from ``config``.
        """
        self.config = config
        self.client = client or openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Reorder ``chunks`` by LLM-judged relevance to ``query``.

        Args:
            query: The search query.
            chunks: Candidate chunks (dicts with at least ``id``, ``text``,
                and the blended ``score`` produced by the retriever).

        Returns:
            The same chunk dicts, reordered by relevance (highest first).
            Scored chunks gain an ``llm_score`` field. On any failure the
            input ordering is preserved.
        """
        if not chunks:
            return chunks

        scored_any = False

        # Score in batches so a large candidate pool never overflows a
        # single prompt/context window.
        for start in range(0, len(chunks), self.config.batch_size):
            batch = chunks[start : start + self.config.batch_size]
            scores = self._score_batch(query, batch)

            if scores:
                scored_any = True
                for chunk in batch:
                    key = str(chunk.get("id"))
                    if key in scores:
                        chunk["llm_score"] = scores[key]

        if not scored_any:
            # Nothing was scored (all batches failed or returned nothing):
            # hand back the exact ordering we were given.
            logger.info("reranker_noop", reason="no_scores", chunk_count=len(chunks))
            return chunks

        # Stable sort by effective score: the LLM score when present,
        # otherwise the chunk's original blended score. Because the input is
        # already blended-sorted, ties preserve the prior order.
        reranked = sorted(chunks, key=self._effective_score, reverse=True)

        logger.info(
            "reranker_complete",
            chunk_count=len(chunks),
            reordered=[c.get("id") for c in reranked] != [c.get("id") for c in chunks],
        )
        return reranked

    @staticmethod
    def _effective_score(chunk: dict) -> float:
        """Score used for ordering: LLM score if judged, else blended score."""
        if "llm_score" in chunk:
            return float(chunk["llm_score"])
        return float(chunk.get("score", 0.0))

    def _score_batch(self, query: str, batch: list[dict]) -> dict[str, float]:
        """Ask the LLM to score one batch of chunks.

        Returns:
            Mapping of ``str(chunk_id) -> clamped score`` for chunks the LLM
            scored. An empty dict signals "fall back" (error, malformed
            output, or no usable scores) -- callers must treat it as a no-op.
        """
        prompt = self._build_prompt(query, batch)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": RERANK_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            content = response.choices[0].message.content
        except Exception as exc:  # network error, timeout, bad response shape
            logger.warning("reranker_llm_call_failed", error=str(exc))
            return {}

        raw_scores = self._parse_scores(content)
        if not raw_scores:
            logger.warning("reranker_unparseable_output", snippet=(content or "")[:120])
            return {}

        # Keep only ids that are actually in this batch; clamp to [0, 1].
        valid_ids = {str(chunk.get("id")) for chunk in batch}
        cleaned: dict[str, float] = {}
        for key, value in raw_scores.items():
            if key not in valid_ids:
                continue  # unknown id -> ignore
            try:
                score = float(value)
            except (TypeError, ValueError):
                continue  # non-numeric score -> ignore this entry
            cleaned[key] = max(0.0, min(1.0, score))

        return cleaned

    @staticmethod
    def _build_prompt(query: str, batch: list[dict]) -> str:
        """Render the scoring prompt for a batch of chunks."""
        lines = []
        for chunk in batch:
            text = (chunk.get("text") or "").replace("\n", " ").strip()
            lines.append(f'- id "{chunk.get("id")}": {text}')
        listing = "\n".join(lines)

        example_id = batch[0].get("id")
        return (
            f"Query:\n{query}\n\n"
            "Rate how relevant each chunk below is to the query, from 0.0 "
            "(irrelevant) to 1.0 (directly relevant). Judge meaning, not just "
            "shared words.\n\n"
            f"Chunks:\n{listing}\n\n"
            "Respond with ONLY a JSON object mapping each id (as a string) to "
            f'its score, e.g. {{"{example_id}": 0.82}}. Include every id once.'
        )

    @staticmethod
    def _parse_scores(raw: str | None) -> dict:
        """Best-effort extraction of a ``{id: score}`` JSON object.

        Tries a fenced ```json block, then the raw string, then the first
        brace-delimited blob. Returns ``{}`` if none parse to a dict.
        """
        if not raw:
            return {}

        candidates: list[str] = []

        fence = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.DOTALL)
        if fence:
            candidates.append(fence.group(1))

        candidates.append(raw)

        brace = re.search(r"\{.*\}", raw, re.DOTALL)
        if brace:
            candidates.append(brace.group(0))

        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(data, dict):
                return data

        return {}
