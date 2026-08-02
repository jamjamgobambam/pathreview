"""LLM-based re-ranker for retrieval chunks."""

import re

import openai
import structlog

logger = structlog.get_logger()


class LLMReranker:
    """Uses an LLM to score and re-rank retrieved chunks."""

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-3.5-turbo"):
        """Initialize the re-ranker with OpenAI client.

        Args:
            api_key: OpenAI API key
            base_url: Base URL for OpenAI/OpenRouter
            model: Model name to use
        """
        self.model = model
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Re-rank chunks based on LLM relevance score.

        Args:
            query: The user's query
            chunks: The retrieved chunks from the hybrid search

        Returns:
            List of chunks re-sorted by LLM score
        """
        if not chunks:
            return []

        reranked_chunks = []

        # Process each chunk individually
        for chunk in chunks:
            text = chunk.get("text", "")

            prompt = (
                f"Given the user query: '{query}'\n\n"
                f"Rate the relevance of the following document chunk from 1 to 10, "
                f"where 1 is completely irrelevant and 10 is perfectly relevant.\n"
                f"Only output the number.\n\n"
                f"Document chunk:\n{text}"
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a search relevance evaluator.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,  # low temperature for consistency
                    max_tokens=10,
                )

                content = response.choices[0].message.content.strip()

                # Extract the first number found in the response
                match = re.search(r"\d+", content)
                if match:
                    llm_score = float(match.group())
                else:
                    logger.warning("reranker_parse_failed", content=content)
                    llm_score = chunk.get("score", 0.0)  # Fallback to original score

            except Exception as e:
                logger.error("reranker_llm_failed", error=str(e))
                llm_score = chunk.get("score", 0.0)  # Fallback to original score

            # Add the new score to the chunk
            chunk_copy = dict(chunk)
            chunk_copy["llm_score"] = llm_score
            reranked_chunks.append(chunk_copy)

        # Sort the chunks by the new llm_score descending
        reranked_chunks.sort(key=lambda x: x.get("llm_score", 0), reverse=True)

        logger.info(
            "llm_reranking_complete",
            query_len=len(query),
            chunk_count=len(reranked_chunks),
        )

        return reranked_chunks
