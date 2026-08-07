"""LLM-based re-ranking of retrieved chunks.

The reranking stage runs on every retrieval. It scores each candidate
chunk's relevance to the query and reorders the top-k before those chunks
reach the generator. The provider behind the stage is selected by the
application's ``llm_provider`` setting: ``"mock"`` yields a deterministic,
network-free reranker for tests/CI, while any other value uses a real LLM.

Reranking is only skipped for the degenerate cases where it is meaningless
(zero or one chunk) or impossible (LLM unreachable), in which case the
original hybrid order is preserved so the pipeline never breaks.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


SYSTEM_PROMPT = (
    "You are a search relevance judge. Given a user query and a list of "
    "candidate text chunks, score how well each chunk answers the query. "
    "Score each chunk from 0 (irrelevant) to 10 (directly answers the query). "
    "Respond with ONLY a JSON object mapping each chunk id to its integer "
    'score, e.g. {"id-1": 8, "id-2": 3}. Do not include any other text.'
)


@dataclass
class RerankConfig:
    """Configuration for the LLM reranker.

    Mirrors ``ReviewConfig`` in the generator. ``temperature`` and
    ``max_tokens`` are reranker-specific defaults and are not environment
    configurable; ``api_key``, ``base_url`` and ``model`` are expected to be
    supplied from the existing ``openrouter_*`` application settings.
    """

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 500


class Reranker(ABC):
    """Abstract base class for chunk rerankers."""

    @abstractmethod
    def rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        """Reorder ``chunks`` by relevance to ``query`` and return the top-k.

        Args:
            query: The text query the chunks were retrieved for.
            chunks: Candidate chunks (dicts with at least ``id`` and ``text``).
            top_k: Maximum number of chunks to return.

        Returns:
            A reordered list of at most ``top_k`` chunks.
        """
        raise NotImplementedError("Subclasses must implement rerank()")

    @staticmethod
    def _is_trivial(chunks: list[dict]) -> bool:
        """Return True when reranking is meaningless (0 or 1 chunk)."""
        return len(chunks) <= 1


class MockReranker(Reranker):
    """Deterministic, network-free reranker for tests and CI.

    Scores each chunk from a stable hash of the query and chunk text, so the
    same inputs always produce the same ordering. This lets tests assert that
    the reranking stage ran and reordered chunks without needing an LLM or an
    API key.
    """

    def rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        if not chunks:
            return []
        if self._is_trivial(chunks):
            return list(chunks[:top_k])

        scored = []
        for chunk in chunks:
            score = self._score(query, chunk.get("text", ""))
            scored.append({**chunk, "rerank_score": score})

        scored.sort(key=lambda c: c["rerank_score"], reverse=True)

        logger.info(
            "rerank_complete",
            provider="mock",
            candidate_count=len(chunks),
            returned_count=min(top_k, len(scored)),
        )
        return scored[:top_k]

    @staticmethod
    def _score(query: str, text: str) -> float:
        """Deterministic pseudo-relevance score in ``[0, 10]``."""
        import hashlib

        digest = hashlib.sha256(f"{query}\x00{text}".encode()).digest()
        # Map the first 4 bytes to a stable float in [0, 10].
        return int.from_bytes(digest[:4], byteorder="big") / 0xFFFFFFFF * 10


class LLMReranker(Reranker):
    """Reranker that prompts an LLM to score chunk relevance.

    The OpenAI-compatible client is injectable so tests can supply a fake and
    exercise the parsing/fallback logic without a network call.
    """

    def __init__(self, config: RerankConfig, client: Any = None):
        """Initialize the reranker.

        Args:
            config: Reranker configuration (API key, base URL, model, ...).
            client: Optional OpenAI-compatible client. When omitted, a real
                ``openai.OpenAI`` client is constructed from ``config``.
        """
        self.config = config
        if client is None:
            import openai

            client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.client = client

    def rerank(self, query: str, chunks: list[dict], top_k: int) -> list[dict]:
        if not chunks:
            return []
        if self._is_trivial(chunks):
            return list(chunks[:top_k])

        try:
            scores = self._score_chunks(query, chunks)
        except Exception as e:
            # Graceful degradation: keep the incoming hybrid order.
            logger.warning("rerank_failed", error=str(e), candidate_count=len(chunks))
            return list(chunks[:top_k])

        ranked = [
            {**chunk, "rerank_score": scores.get(chunk.get("id", ""), 0.0)} for chunk in chunks
        ]
        ranked.sort(key=lambda c: c["rerank_score"], reverse=True)

        logger.info(
            "rerank_complete",
            provider="llm",
            model=self.config.model,
            candidate_count=len(chunks),
            returned_count=min(top_k, len(ranked)),
        )
        return ranked[:top_k]

    def _score_chunks(self, query: str, chunks: list[dict]) -> dict[str, float]:
        """Call the LLM and return a mapping of chunk id -> relevance score."""
        prompt = self._build_prompt(query, chunks)

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        content = response.choices[0].message.content
        return self._parse_scores(content)

    @staticmethod
    def _build_prompt(query: str, chunks: list[dict]) -> str:
        """Render the query and candidate chunks into the user prompt."""
        parts = [f"Query: {query}", "", "Chunks:"]
        for chunk in chunks:
            chunk_id = chunk.get("id", "")
            text = chunk.get("text", "").replace("\n", " ").strip()
            # Truncate to keep the prompt bounded for the small model.
            if len(text) > 500:
                text = text[:500] + "..."
            parts.append(f"- id: {chunk_id}\n  text: {text}")
        return "\n".join(parts)

    @staticmethod
    def _parse_scores(content: str | None) -> dict[str, float]:
        """Parse the LLM response into a ``{id: score}`` mapping.

        Tolerant of models that wrap the JSON in prose or code fences. Raises
        ``ValueError`` if no JSON object can be recovered so the caller falls
        back to the original order.
        """
        if not content:
            raise ValueError("empty rerank response")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise ValueError("no JSON object found in rerank response") from None
            data = json.loads(match.group(0))

        if not isinstance(data, dict):
            raise ValueError("rerank response was not a JSON object")

        scores: dict[str, float] = {}
        for chunk_id, score in data.items():
            try:
                scores[str(chunk_id)] = float(score)
            except (TypeError, ValueError):
                # Skip unparseable entries; missing ids default to 0 later.
                continue
        return scores


def get_reranker(provider_name: str, config: RerankConfig | None = None) -> Reranker:
    """Factory returning a reranker for the given provider.

    Args:
        provider_name: Application ``llm_provider`` value ("mock" or a real
            provider such as "openai"/"openrouter").
        config: Required for non-mock providers; supplies the API credentials
            and model.

    Returns:
        A ``Reranker`` instance.

    Raises:
        ValueError: If a non-mock provider is requested without a config.
    """
    name = provider_name.lower().strip()
    if name == "mock":
        return MockReranker()
    if config is None:
        raise ValueError(f"RerankConfig is required for the '{provider_name}' reranker provider")
    return LLMReranker(config)
