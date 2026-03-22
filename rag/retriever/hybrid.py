"""Hybrid retriever combining vector and keyword search."""

import structlog
from .vector_store import VectorStore
from .keyword_search import KeywordSearcher

logger = structlog.get_logger()


class HybridRetriever:
    """Combines vector similarity and BM25 keyword search."""

    def __init__(self, vector_store: VectorStore, keyword_searcher: KeywordSearcher,
                 vector_weight: float = 0.7, keyword_weight: float = 0.3):
        """Initialize hybrid retriever.

        Args:
            vector_store: VectorStore instance
            keyword_searcher: KeywordSearcher instance
            vector_weight: Weight for vector scores (0-1)
            keyword_weight: Weight for keyword scores (0-1)
        """
        self.vector_store = vector_store
        self.keyword_searcher = keyword_searcher
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    def retrieve(self, query: str, profile_id: str, query_embedding: list[float],
                 max_chunks: int = 10, min_score: float = 0.3) -> list[dict]:
        """Retrieve chunks using hybrid approach.

        Args:
            query: Text query
            profile_id: Profile identifier for collection selection
            query_embedding: Embedding vector for query
            max_chunks: Maximum chunks to return
            min_score: Minimum score threshold (0-1)

        Returns:
            List of dicts with blended scores
        """
        collection_name = f"profile_{profile_id}"

        # Vector search
        vector_results = self.vector_store.query(
            query_embedding, collection_name, n_results=max_chunks * 2
        )

        # Keyword search - need to fetch all chunks first
        all_chunks = self._get_all_chunks(collection_name)
        keyword_results = self.keyword_searcher.search(query, top_k=max_chunks * 2)

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
                vector_score = (vector_map[chunk_id]["score"] / vector_scores_max) if vector_scores_max > 0 else 0
                base_chunk = vector_map[chunk_id]
            else:
                base_chunk = keyword_map[chunk_id]

            if chunk_id in keyword_map:
                keyword_score = (keyword_map[chunk_id].get("bm25_score", 0) / keyword_scores_max) if keyword_scores_max > 0 else 0

            blended_score = (
                self.vector_weight * vector_score +
                self.keyword_weight * keyword_score
            )

            blended[chunk_id] = {
                "id": chunk_id,
                "text": base_chunk.get("text", ""),
                "metadata": base_chunk.get("metadata", {}),
                "score": blended_score,
                "vector_score": vector_score,
                "keyword_score": keyword_score
            }

        # Filter by min_score and sort
        results = [r for r in blended.values() if r["score"] >= min_score]
        results.sort(key=lambda x: x["score"], reverse=True)

        # Return top max_chunks
        final_results = results[:max_chunks]

        logger.info("hybrid_retrieval_complete", query_len=len(query),
                   vector_results=len(vector_results), keyword_results=len(keyword_results),
                   blended_count=len(blended), filtered_count=len(results),
                   final_count=len(final_results))

        return final_results

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
            all_docs["ids"],
            all_docs["documents"],
            all_docs["metadatas"]
        ):
            chunks.append({
                "id": doc_id,
                "text": text,
                "metadata": metadata
            })
        return chunks
