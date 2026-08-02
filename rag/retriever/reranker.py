"""LLM-based re-ranker for RAG retrieval."""

import json
from typing import Any

import openai
import structlog

logger = structlog.get_logger()


class LLMReranker:
    """Uses an LLM to score retrieved chunks by query relevance."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        client: Any | None = None,
    ):
        """Initialize LLMReranker.

        Args:
            api_key: OpenAI API key (optional if client is passed)
            base_url: Custom API base URL
            model: Model name for re-ranking scoring
            client: Optional pre-configured OpenAI or compatible client object
        """
        self.model = model
        if client is not None:
            self.client = client
        elif api_key:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None

    def score_chunks(self, query: str, chunks: list[dict]) -> list[dict]:
        """Score a list of text chunks based on relevance to the query.

        Args:
            query: User search/prompt query string
            chunks: List of chunk dicts containing 'id' and 'text' keys

        Returns:
            List of chunk dicts updated with 'rerank_score' key.
        """
        if not chunks:
            return []

        if self.client is None:
            logger.warning(
                "reranker_no_client",
                msg="No LLM client configured, skipping re-ranking.",
            )
            for chunk in chunks:
                chunk["rerank_score"] = chunk.get("score", 0.0)
            return chunks

        # Format prompt with candidate chunks
        formatted_chunks = []
        for idx, chunk in enumerate(chunks, 1):
            formatted_chunks.append(f"[{idx}] ID: {chunk['id']}\nContent: {chunk.get('text', '')}")

        candidates_text = "\n\n".join(formatted_chunks)

        prompt = (
            f"You are a relevance evaluator for a portfolio review system.\n"
            f"Query: {query}\n\n"
            f"Evaluate how relevant each candidate chunk is to answering the query.\n"
            f"Assign a relevance score from 0.0 to 1.0 for each chunk.\n\n"
            f"Candidates:\n{candidates_text}\n\n"
            f"Respond ONLY with a valid JSON array of objects, where each object has:\n"
            f'  "id": chunk ID string\n'
            f'  "score": float between 0.0 and 1.0\n'
            f'Example output format: [{{"id": "chunk-1", "score": 0.9}}]'
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise relevance evaluator. Output valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )

            raw_text = response.choices[0].message.content or ""
            parsed_scores = self._parse_scores(raw_text)

            # Map scores back to chunks
            score_map = {
                item["id"]: float(item["score"])
                for item in parsed_scores
                if "id" in item and "score" in item
            }

            scored_chunks = []
            for chunk in chunks:
                chunk_copy = dict(chunk)
                # If LLM provided a score, use it; otherwise fallback to existing score
                chunk_copy["rerank_score"] = score_map.get(chunk["id"], chunk.get("score", 0.0))
                scored_chunks.append(chunk_copy)

            return scored_chunks

        except Exception as e:
            logger.warning("reranker_failed_fallback", error=str(e))
            # Fallback gracefully to original candidate scores
            fallback_chunks = []
            for chunk in chunks:
                chunk_copy = dict(chunk)
                chunk_copy["rerank_score"] = chunk.get("score", 0.0)
                fallback_chunks.append(chunk_copy)
            return fallback_chunks

    def rerank(self, query: str, chunks: list[dict], top_k: int = 10) -> list[dict]:
        """Rerank candidates and return the top-k most relevant chunks.

        Args:
            query: User search query
            chunks: Candidate chunks
            top_k: Number of top chunks to return

        Returns:
            Filtered and sorted top-k chunk list
        """
        scored_chunks = self.score_chunks(query, chunks)
        # Sort by rerank_score descending
        scored_chunks.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def _parse_scores(text: str) -> list[dict]:
        """Extract and parse JSON array from LLM response text.

        Args:
            text: LLM response string

        Returns:
            Parsed list of dict objects
        """
        cleaned = text.strip()
        # Handle markdown code blocks
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and isinstance(data.get("scores"), list):
                scores: list[dict] = data["scores"]
                return scores
            return []
        except Exception:
            return []
