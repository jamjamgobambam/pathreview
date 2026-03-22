import hashlib
from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        raise NotImplementedError("Subclasses must implement embed()")


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock embedding provider for testing.

    Returns deterministic fake embeddings based on text hash.
    Same text always produces the same embedding vector.
    """

    EMBEDDING_DIM = 1536

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate deterministic mock embeddings.

        Args:
            texts: List of text strings to embed

        Returns:
            List of 1536-dimensional embedding vectors
        """
        embeddings = []

        for text in texts:
            # Create deterministic seed from text hash
            text_hash = hashlib.sha256(text.encode()).digest()
            seed = int.from_bytes(text_hash[:4], byteorder="big")

            # Generate consistent random vector
            rng = np.random.RandomState(seed)
            embedding = rng.normal(0, 1, self.EMBEDDING_DIM)

            # Normalize
            embedding = embedding / np.linalg.norm(embedding)

            embeddings.append(embedding.tolist())

        return embeddings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider using text-embedding-3-small model.

    Requires OPENAI_API_KEY environment variable.
    """

    MODEL = "text-embedding-3-small"

    def __init__(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI()
        except ImportError:
            raise ImportError("openai package is required for OpenAIEmbeddingProvider")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings using OpenAI API.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.MODEL,
            input=texts,
        )

        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]
        return embeddings


def get_embedding_provider(provider_name: str) -> EmbeddingProvider:
    """
    Factory function to get an embedding provider by name.

    Args:
        provider_name: One of "mock", "openai"

    Returns:
        Appropriate EmbeddingProvider instance

    Raises:
        ValueError: If provider_name is not recognized
    """
    provider_name_lower = provider_name.lower().strip()

    if provider_name_lower == "mock":
        return MockEmbeddingProvider()
    elif provider_name_lower == "openai":
        return OpenAIEmbeddingProvider()
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider_name}. "
            "Supported: 'mock', 'openai'"
        )
