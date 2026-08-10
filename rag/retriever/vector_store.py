"""ChromaDB-backed vector store for semantic retrieval."""

import chromadb
from chromadb.config import Settings
import structlog

logger = structlog.get_logger()


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

        Chunk identity is read from ``Chunk.metadata`` because ``Chunk`` is a
        two-field dataclass (``text``, ``metadata``) and the chunkers put
        ``source_id`` and ``chunk_index`` inside that metadata. The derived id
        matches the convention ``BatchEmbeddingProcessor`` already writes
        (``{source_id}_chunk_{chunk_index}``), so both indexing paths address
        the same documents instead of diverging.

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
            metadata = chunk.metadata or {}
            source_id = metadata.get("source_id", "unknown")
            chunk_index = metadata.get("chunk_index", 0)

            ids.append(f"{source_id}_chunk_{chunk_index}")
            embeddings.append(embedding)
            documents.append(chunk.text)
            metadatas.append({
                "source_id": source_id,
                "chunk_index": chunk_index,
                "section": metadata.get("section") or "",
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
