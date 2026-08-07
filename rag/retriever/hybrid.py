"""Hybrid retriever combining vector and keyword search."""

from typing import Any

import structlog

from .keyword_search import KeywordSearcher
from .reranker import LLMReranker
from .vector_store import VectorStore

logger = structlog.get_logger()


class HybridRetriever:
    """Combines vector similarity and BM25 keyword search."""

    def __init__(
        self,
        vector_store: VectorStore,
        keyword_searcher: KeywordSearcher,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        reranker: LLMReranker | None = None,
        rerank_candidate_multiplier: int = 3,
    ):
        """Initialize hybrid retriever.

        Args:
            vector_store: VectorStore instance
            keyword_searcher: KeywordSearcher instance
            vector_weight: Weight for vector scores (0-1)
            keyword_weight: Weight for keyword scores (0-1)
            reranker: Optional LLMReranker used when ``rerank=True``
            rerank_candidate_multiplier: Candidate pool size multiplier fed to
                the re-ranker (over-fetch factor over ``max_chunks``)
        """
        self.vector_store = vector_store
        self.keyword_searcher = keyword_searcher
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.reranker = reranker
        self.rerank_candidate_multiplier = rerank_candidate_multiplier

    def retrieve(
        self,
        query: str,
        profile_id: str,
        query_embedding: list[float],
        max_chunks: int = 10,
        min_score: float = 0.3,
        rerank: bool = False,
    ) -> list[dict]:
        """Retrieve chunks using hybrid approach.

        Args:
            query: Text query
            profile_id: Profile identifier for collection selection
            query_embedding: Embedding vector for query
            max_chunks: Maximum chunks to return
            min_score: Minimum score threshold (0-1)
            rerank: When True and a reranker is configured, re-rank the
                candidate pool by LLM relevance before selecting top-k

        Returns:
            List of dicts with blended scores
        """
        collection_name = f"profile_{profile_id}"

        # When re-ranking, fetch a wider candidate pool so the LLM has more
        # than the final top-k to reorder; otherwise keep the original 2x pool.
        use_rerank = bool(rerank and self.reranker)
        fetch_k = max_chunks * (self.rerank_candidate_multiplier if use_rerank else 2)

        # Vector search
        vector_results = self.vector_store.query(
            query_embedding, collection_name, n_results=fetch_k
        )

        # Keyword search
        keyword_results = self.keyword_searcher.search(query, top_k=fetch_k)

        # Create id-to-chunk mapping for both approaches
        vector_map = {r["id"]: r for r in vector_results}
        keyword_map = {r.get("id", ""): r for r in keyword_results}

        # Normalize scores to 0-1
        vector_scores_max = max([r["score"] for r in vector_results], default=1.0)
        keyword_scores_max = max([r.get("bm25_score", 0) for r in keyword_results], default=1.0)

        # Blend results
        blended = {}
        all_ids = set(vector_map.keys()) | set(keyword_map.keys())

        for chunk_id in all_ids:
            vector_score = 0.0
            keyword_score = 0.0

            if chunk_id in vector_map:
                vector_score = (
                    (vector_map[chunk_id]["score"] / vector_scores_max)
                    if vector_scores_max > 0
                    else 0
                )
                base_chunk = vector_map[chunk_id]
            else:
                base_chunk = keyword_map[chunk_id]

            if chunk_id in keyword_map:
                keyword_score = (
                    (keyword_map[chunk_id].get("bm25_score", 0) / keyword_scores_max)
                    if keyword_scores_max > 0
                    else 0
                )

            blended_score = self.vector_weight * vector_score + self.keyword_weight * keyword_score

            blended[chunk_id] = {
                "id": chunk_id,
                "text": base_chunk.get("text", ""),
                "metadata": base_chunk.get("metadata", {}),
                "score": blended_score,
                "vector_score": vector_score,
                "keyword_score": keyword_score,
            }

        # Filter by min_score and sort
        results = [r for r in blended.values() if r["score"] >= min_score]
        results.sort(key=lambda x: x["score"], reverse=True)

        # Optionally re-rank the fetched candidate pool by LLM relevance,
        # otherwise return the top max_chunks by blended score (unchanged).
        if use_rerank:
            final_results = self.reranker.rerank(query, results, top_k=max_chunks)
        else:
            final_results = results[:max_chunks]

        logger.info(
            "hybrid_retrieval_complete",
            query_len=len(query),
            vector_results=len(vector_results),
            keyword_results=len(keyword_results),
            blended_count=len(blended),
            filtered_count=len(results),
            reranked=use_rerank,
            final_count=len(final_results),
        )

        return final_results


def build_hybrid_retriever(
    vector_store: VectorStore,
    keyword_searcher: KeywordSearcher,
    settings: Any,
    client: Any = None,
) -> HybridRetriever:
    """Construct a HybridRetriever with re-ranking wired from settings.

    Consumes the opt-in re-ranking settings: attaches an ``LLMReranker`` only
    when ``settings.enable_reranking`` is True, and passes through
    ``settings.rerank_candidate_multiplier``. When disabled, the returned
    retriever behaves exactly as the non-reranking path.

    Note: the production RAG pipeline is currently a stub
    (``core/services/review_service._run_rag_retrieval_generation``), so no
    live call site builds the retriever yet. This factory is the intended
    integration point once that pipeline is implemented; callers still opt in
    per request via ``retrieve(..., rerank=settings.enable_reranking)``.

    Args:
        vector_store: VectorStore instance.
        keyword_searcher: KeywordSearcher instance.
        settings: Settings exposing enable_reranking, rerank_model,
            rerank_candidate_multiplier, and OpenRouter credentials.
        client: Optional pre-built OpenAI-style client (injected in tests).

    Returns:
        A configured HybridRetriever.
    """
    reranker = (
        LLMReranker.from_settings(settings, client=client) if settings.enable_reranking else None
    )
    return HybridRetriever(
        vector_store,
        keyword_searcher,
        reranker=reranker,
        rerank_candidate_multiplier=settings.rerank_candidate_multiplier,
    )
