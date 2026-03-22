import structlog

from ..chunking.base import Chunk
from .provider import EmbeddingProvider


logger = structlog.get_logger()


class BatchEmbeddingProcessor:
    """Process chunks into embeddings in batches."""

    BATCH_SIZE = 100

    def __init__(self, embedding_provider: EmbeddingProvider, vector_db):
        """
        Initialize the batch processor.

        Args:
            embedding_provider: EmbeddingProvider instance for generating embeddings
            vector_db: ChromaDB collection or database interface
        """
        self.embedding_provider = embedding_provider
        self.vector_db = vector_db

    def process(self, chunks: list[Chunk]) -> list[tuple[Chunk, str]]:
        """
        Process chunks into embeddings and store in vector DB.

        Args:
            chunks: List of Chunk objects to embed

        Returns:
            List of (chunk, embedding_id) tuples

        Raises:
            RuntimeError: If embedding or storage fails
        """
        if not chunks:
            logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")
            return []

        results = []
        total_chunks = len(chunks)

        logger.info("Starting batch embedding processing", chunk_count=total_chunks)

        # Process in batches
        for batch_start in range(0, len(chunks), self.BATCH_SIZE):
            batch_end = min(batch_start + self.BATCH_SIZE, len(chunks))
            batch = chunks[batch_start:batch_end]

            logger.info(
                "Processing embedding batch",
                batch_num=batch_start // self.BATCH_SIZE + 1,
                batch_start=batch_start,
                batch_end=batch_end,
                total=total_chunks,
            )

            # Extract text from chunks
            texts = [chunk.text for chunk in batch]

            try:
                # Generate embeddings
                embeddings = self.embedding_provider.embed(texts)
                logger.info("Generated embeddings for batch", embedding_count=len(embeddings))

                # Store in vector DB
                for chunk, embedding in zip(batch, embeddings):
                    try:
                        embedding_id = self._store_embedding(chunk, embedding)
                        results.append((chunk, embedding_id))
                    except Exception as e:
                        logger.error(
                            "Failed to store embedding",
                            error=str(e),
                            chunk_metadata=chunk.metadata,
                        )
                        raise

            except Exception as e:
                logger.error(
                    "Failed to generate embeddings for batch",
                    error=str(e),
                    batch_start=batch_start,
                    batch_end=batch_end,
                )
                raise

        logger.info("Batch embedding processing complete", stored_count=len(results))
        return results

    def _store_embedding(self, chunk: Chunk, embedding: list[float]) -> str:
        """
        Store an embedding in the vector database.

        Args:
            chunk: The Chunk object
            embedding: The embedding vector

        Returns:
            The ID of the stored embedding
        """
        # Create a unique ID for this embedding
        source_id = chunk.metadata.get("source_id", "unknown")
        chunk_index = chunk.metadata.get("chunk_index", 0)
        embedding_id = f"{source_id}_chunk_{chunk_index}"

        # Store in ChromaDB
        self.vector_db.add(
            ids=[embedding_id],
            embeddings=[embedding],
            metadatas=[chunk.metadata],
            documents=[chunk.text],
        )

        logger.debug("Stored embedding in vector DB", embedding_id=embedding_id)
        return embedding_id
