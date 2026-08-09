"""Hybrid retriever combining vector and keyword search."""

import structlog

from .keyword_search import KeywordSearcher
from .vector_store import VectorStore

logger = structlog.get_logger()


class HybridRetriever:
    """Combines vector similarity and BM25 keyword search via weighted
    Reciprocal Rank Fusion (RRF).

    Scores are blended by rank position rather than raw magnitude, so an
    outlier score on one side (e.g. a BM25 score inflated by a chunk that
    repeats query terms many times) can't set the scale for the whole batch
    the way magnitude-based normalization can.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        keyword_searcher: KeywordSearcher,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 10,
    ):
        """Initialize hybrid retriever.

        Args:
            vector_store: VectorStore instance
            keyword_searcher: KeywordSearcher instance
            vector_weight: Weight applied to the vector-search RRF term (0-1)
            keyword_weight: Weight applied to the keyword-search RRF term (0-1)
            rrf_k: RRF rank-damping constant. Smaller values give top ranks
                more relative influence over the blended score.
        """
        self.vector_store = vector_store
        self.keyword_searcher = keyword_searcher
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        profile_id: str,
        query_embedding: list[float],
        max_chunks: int = 10,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Retrieve chunks using hybrid approach.

        Args:
            query: Text query
            profile_id: Profile identifier for collection selection
            query_embedding: Embedding vector for query
            max_chunks: Maximum chunks to return
            min_score: Minimum blended RRF score threshold. RRF scores are
                small, always-positive, rank-derived values rather than 0-1
                relevance percentages -- use max_chunks to control result
                count; this is a low-level escape hatch, not a relevance cutoff.

        Returns:
            List of dicts with blended scores, ranked highest first
        """
        collection_name = f"profile_{profile_id}"

        # Vector search
        vector_results = self.vector_store.query(
            query_embedding, collection_name, n_results=max_chunks * 2
        )

        # Keyword search - need to fetch all chunks first
        self._get_all_chunks(collection_name)
        keyword_results = self.keyword_searcher.search(query, top_k=max_chunks * 2)

        # Create id-to-chunk mapping for both approaches
        vector_map = {r["id"]: r for r in vector_results}
        keyword_map = {r.get("id", ""): r for r in keyword_results}

        # Rank each side independently (rank 1 = best), with a deterministic
        # tie-break so ordering doesn't depend on Python's hash-randomized
        # set/dict iteration order for string keys.
        vector_ranks = self._rank_map(vector_results, "score")
        keyword_ranks = self._rank_map(keyword_results, "bm25_score")

        # A chunk absent from one side's results ties for that side's worst
        # rank -- it simply fell outside that method's top max_chunks * 2 window.
        worst_vector_rank = len(vector_results) + 1
        worst_keyword_rank = len(keyword_results) + 1

        # Blend via weighted Reciprocal Rank Fusion.
        blended = {}
        all_ids = set(vector_map.keys()) | set(keyword_map.keys())

        for chunk_id in all_ids:
            base_chunk = vector_map.get(chunk_id) or keyword_map[chunk_id]

            vector_rank = vector_ranks.get(chunk_id, worst_vector_rank)
            keyword_rank = keyword_ranks.get(chunk_id, worst_keyword_rank)

            vector_rrf = 1.0 / (self.rrf_k + vector_rank)
            keyword_rrf = 1.0 / (self.rrf_k + keyword_rank)

            blended_score = self.vector_weight * vector_rrf + self.keyword_weight * keyword_rrf

            blended[chunk_id] = {
                "id": chunk_id,
                "text": base_chunk.get("text", ""),
                "metadata": base_chunk.get("metadata", {}),
                "score": blended_score,
                "vector_score": vector_rrf,
                "keyword_score": keyword_rrf,
            }

        # Filter by min_score and sort, breaking ties on id for determinism
        results = [r for r in blended.values() if r["score"] >= min_score]
        results.sort(key=lambda x: (-x["score"], x["id"]))

        # Return top max_chunks
        final_results = results[:max_chunks]

        logger.info(
            "hybrid_retrieval_complete",
            query_len=len(query),
            vector_results=len(vector_results),
            keyword_results=len(keyword_results),
            blended_count=len(blended),
            filtered_count=len(results),
            final_count=len(final_results),
        )

        return final_results

    @staticmethod
    def _rank_map(results: list[dict], score_key: str) -> dict[str, int]:
        """Map each result's chunk id to its 1-indexed rank (1 = highest score).

        Ties are broken by chunk id for determinism, since ranking must not
        depend on Python's hash-randomized set/dict iteration order.

        Args:
            results: Scored results, each with an 'id' field and score_key field
            score_key: Dict key holding the score to rank by

        Returns:
            Mapping of chunk id to rank
        """
        ordered = sorted(results, key=lambda r: (-r.get(score_key, 0), r["id"]))
        return {r["id"]: rank for rank, r in enumerate(ordered, start=1)}

    def _get_all_chunks(self, collection_name: str) -> list[dict]:
        """Fetch all chunks in a collection (for keyword indexing).

        Args:
            collection_name: Collection name

        Returns:
            List of chunk dicts
        """
        collection = self.vector_store.get_collection(collection_name)
        all_docs = collection.get(include=["documents", "metadatas"])

        chunks = []
        for doc_id, text, metadata in zip(
            all_docs["ids"], all_docs["documents"], all_docs["metadatas"], strict=False
        ):
            chunks.append({"id": doc_id, "text": text, "metadata": metadata})
        return chunks
