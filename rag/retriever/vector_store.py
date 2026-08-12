"""ChromaDB-backed vector store for semantic retrieval."""

import chromadb
from chromadb.config import Settings
import structlog

logger = structlog.get_logger()


def collection_name_for_profile(profile_id: object) -> str:
    """Build the ChromaDB collection name that holds a profile's embeddings.

    This is the single source of truth for the per-profile collection name.
    Both the retrieval path and the profile-delete cleanup path must agree on
    this format, so they both call this helper instead of hardcoding it.

    Args:
        profile_id: Profile identifier (UUID or str).

    Returns:
        The collection name, e.g. ``"profile_<id>"``.
    """
    return f"profile_{profile_id}"


class VectorStore:
    """Wrapper around ChromaDB for vector similarity search."""

    def __init__(self, persist_dir: str = ".chromadb"):
        """Initialize ChromaDB client.

        Args:
            persist_dir: Directory to persist vector store
        """
        self.client = chromadb.PersistentClient(path=persist_dir)

    def get_collection(self, name: str):
        """Get or create a collection.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_collection(name=name)
            logger.info("retrieved_collection", collection_name=name)
        except Exception:
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("created_collection", collection_name=name)
        return collection

    def add_chunks(self, chunks_with_embeddings: list[tuple], collection_name: str) -> None:
        """Add chunks with embeddings to vector store.

        Args:
            chunks_with_embeddings: List of (Chunk, embedding_vector) tuples
            collection_name: Name of collection to add to
        """
        collection = self.get_collection(collection_name)

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for chunk, embedding in chunks_with_embeddings:
            ids.append(chunk.id)
            embeddings.append(embedding)
            documents.append(chunk.text)
            metadatas.append({
                "source_id": chunk.source_id,
                "chunk_index": chunk.chunk_index,
                "section": chunk.section or "",
            })

        if ids:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info("added_chunks", count=len(ids), collection=collection_name)

    def query(self, query_embedding: list[float], collection_name: str,
              n_results: int = 10) -> list[dict]:
        """Search for similar vectors.

        Args:
            query_embedding: Query embedding vector
            collection_name: Collection to search
            n_results: Number of results to return

        Returns:
            List of dicts with text, metadata, score, id
        """
        collection = self.get_collection(collection_name)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["embeddings", "documents", "metadatas", "distances"]
        )

        retrieved = []
        if results["documents"] and len(results["documents"]) > 0:
            for doc, metadata, distance, chunk_id in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
                results["ids"][0]
            ):
                # ChromaDB distances are euclidean by default; convert to similarity score
                similarity = 1 / (1 + distance)
                retrieved.append({
                    "id": chunk_id,
                    "text": doc,
                    "metadata": metadata,
                    "score": similarity
                })

        logger.info("vector_query_complete", collection=collection_name,
                   results_count=len(retrieved))
        return retrieved

    def delete_by_source_id(self, source_id: str, collection_name: str) -> None:
        """Delete all chunks from a source (for re-ingestion).

        Args:
            source_id: Source identifier
            collection_name: Collection to delete from
        """
        collection = self.get_collection(collection_name)

        # Get all documents and filter by source_id
        all_docs = collection.get(
            where={"source_id": {"$eq": source_id}}
        )

        if all_docs["ids"]:
            collection.delete(ids=all_docs["ids"])
            logger.info("deleted_by_source", source_id=source_id,
                       count=len(all_docs["ids"]), collection=collection_name)

    def delete_collection(self, name: str) -> None:
        """Delete an entire collection and all embeddings it contains.

        Used when a profile is deleted, to remove its per-profile collection so
        no orphaned vectors are left behind (issue #80). The operation is
        idempotent: deleting a collection that does not exist is treated as a
        no-op rather than an error, so it is safe to call for profiles that
        never had any embeddings ingested.

        Args:
            name: Name of the collection to delete.
        """
        try:
            self.client.delete_collection(name=name)
            logger.info("deleted_collection", collection_name=name)
        except Exception:
            # ChromaDB raises when the collection doesn't exist. That's a
            # legitimate no-op here (profile had no embeddings), so swallow it.
            logger.info("delete_collection_noop", collection_name=name)
