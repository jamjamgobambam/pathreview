"""LLM-based chunk reranker for improving retrieval relevance."""

import json
from dataclasses import dataclass

import openai
import structlog

logger = structlog.get_logger()

RERANK_PROMPT = """You are a relevance scorer. \
Given a query and a text chunk, rate how relevant the chunk is to answering the query.

Query: {query}

Chunk:
{chunk_text}

Rate the relevance from 0 to 10 where:
- 0 means completely irrelevant
- 5 means somewhat relevant
- 10 means directly answers the query

Respond with ONLY a JSON object: {{"score": <number>}}"""

BATCH_RERANK_PROMPT = """You are a relevance scorer. \
Given a query and a list of text chunks, rate how relevant each chunk is to answering the query.

Query: {query}

Chunks:
{chunks_formatted}

For each chunk, rate relevance from 0 to 10 where:
- 0 means completely irrelevant
- 5 means somewhat relevant
- 10 means directly answers the query

Respond with ONLY a JSON array of objects: [{{"index": 0, "score": <number>}}, ...]"""


@dataclass
class RerankerConfig:
    """Configuration for the LLM reranker."""

    api_key: str
    base_url: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.0
    max_tokens: int = 500
    batch_size: int = 10
    relevance_threshold: float = 3.0


class ChunkReranker:
    """Reranks retrieved chunks using an LLM relevance score."""

    def __init__(self, config: RerankerConfig):
        """Initialize the reranker.

        Args:
            config: RerankerConfig with API settings and scoring parameters
        """
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    def rerank(self, query: str, chunks: list[dict], top_k: int | None = None) -> list[dict]:
        """Rerank chunks by LLM-scored relevance to the query.

        Args:
            query: The retrieval query
            chunks: List of chunk dicts with 'id', 'text', 'metadata', 'score'
            top_k: Number of top chunks to return (defaults to len(chunks))

        Returns:
            Reranked list of chunks sorted by LLM relevance score
        """
        if not chunks:
            return []

        if top_k is None:
            top_k = len(chunks)

        scored_chunks = self._batch_score(query, chunks)

        scored_chunks = [
            c for c in scored_chunks if c["rerank_score"] >= self.config.relevance_threshold
        ]
        scored_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)

        return scored_chunks[:top_k]

    def _batch_score(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score chunks in batches using the LLM.

        Args:
            query: The retrieval query
            chunks: List of chunk dicts

        Returns:
            Chunks with 'rerank_score' field added
        """
        results = []
        for i in range(0, len(chunks), self.config.batch_size):
            batch = chunks[i : i + self.config.batch_size]
            batch_scores = self._score_batch(query, batch)
            results.extend(batch_scores)
        return results

    def _score_batch(self, query: str, batch: list[dict]) -> list[dict]:
        """Score a single batch of chunks.

        Args:
            query: The retrieval query
            batch: Batch of chunk dicts

        Returns:
            Batch with rerank_score added to each chunk
        """
        chunks_formatted = "\n\n".join(
            f"[{i}] {chunk.get('text', '')[:500]}" for i, chunk in enumerate(batch)
        )

        prompt = BATCH_RERANK_PROMPT.format(query=query, chunks_formatted=chunks_formatted)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            content = response.choices[0].message.content or ""
            scores = self._parse_batch_response(content, len(batch))
        except (openai.APIError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("reranker_batch_failed", error=str(e))
            scores = [chunk.get("score", 0.0) * 10.0 for chunk in batch]

        scored_batch = []
        for chunk, score in zip(batch, scores, strict=False):
            scored_chunk = dict(chunk)
            scored_chunk["rerank_score"] = score
            scored_batch.append(scored_chunk)

        return scored_batch

    def _parse_batch_response(self, content: str, expected_count: int) -> list[float]:
        """Parse the LLM batch scoring response.

        Args:
            content: Raw LLM response text
            expected_count: Number of scores expected

        Returns:
            List of float scores, one per chunk
        """
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        parsed = json.loads(content)

        if isinstance(parsed, list):
            scores = [0.0] * expected_count
            for item in parsed:
                idx = item.get("index", -1)
                if 0 <= idx < expected_count:
                    scores[idx] = float(item.get("score", 0.0))
            return scores

        raise ValueError(f"Unexpected response format: {type(parsed)}")
