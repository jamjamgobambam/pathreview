import structlog
import logging
from typing import Any
from ..chunking.base import Chunk
from .provider import EmbeddingProvider

logger = structlog.get_logger()
#logger = logging.getLogger("path_review")

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
        self._count = 1

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
        debug = self.debug
        if not chunks:
            debug(f"CHUNKS IS NULL: {chunks}")
            logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")
            return []

        results = []
        total_chunks = len(chunks)
        debug(f"TOTAL CHUNKS COUNT: {total_chunks}")
        logger.info("Starting batch embedding processing", chunk_count=total_chunks)

        # Process in batches
        for batch_start in range(0, len(chunks), self.BATCH_SIZE):
            debug(f"CURRENT BATCH START: {batch_start}")
            batch_end = min(batch_start + self.BATCH_SIZE, len(chunks))
            batch = chunks[batch_start:batch_end]
            debug(f"CURRENT BATCH END: {batch_end}")
            debug(f"CURRENT BATCH: {batch}")
            logger.info(
                "Processing embedding batch",
                batch_num=batch_start // self.BATCH_SIZE + 1,
                batch_start=batch_start,
                batch_end=batch_end,
                total=total_chunks,
            )

            # Extract text from chunks
            texts = [chunk.text for chunk in batch]
            debug(f"TEXTS INSIDE CHUNK: {texts}")
            try:
                # Generate embeddings
                embeddings = self.embedding_provider.embed(texts)
                debug(f"EMBEDDINGS: {len(embedding)}")
                logger.info("Generated embeddings for batch", embedding_count=len(embeddings))

                # Store in vector DB
                for chunk, embedding in zip(batch, embeddings):
                    debug(f"CURRENT CHUNK AND EMBEDDING: \n CHUNK: {chunk} \n EMBEDDING: {embedding}")
                    try:
                        embedding_id = self._store_embedding(chunk, embedding)
                        c = (chunk, embedding_id)
                        results.append(c)
                        debug(f"ADDED TO RESULTS: {c}")
                    except Exception as e:
                        logger.error(
                            "Failed to store embedding",
                            error=str(e),
                            chunk_metadata=chunk.metadata,
                        )
                        debug(f"ERROR WAS HIT: {e}")
                        raise

            except Exception as e:
                logger.error(
                    "Failed to generate embeddings for batch",
                    error=str(e),
                    batch_start=batch_start,
                    batch_end=batch_end,
                )
                debug(f"ERROR WAS HIT: {e}")
                raise

        logger.info("Batch embedding processing complete", stored_count=len(results))
        debug(f"STORED COUNT: {len(results)}")
        self._reset()
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

    def debug(self, info:Any):
        print()
        print("====================================================")
        print(f"\n[DEBUG {self._count}] \n\t\u2022 {info}\n")
        print("====================================================")
        print()
        self._count += 1
    
    def _reset(self):
        self._count = 1