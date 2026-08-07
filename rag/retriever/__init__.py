"""Retriever module for RAG pipeline."""

from .hybrid import HybridRetriever
from .reranker import ChunkReranker, RerankerConfig

__all__ = ["HybridRetriever", "ChunkReranker", "RerankerConfig", "build_reranker_from_settings"]


def build_reranker_from_settings() -> ChunkReranker | None:
    """Create a ChunkReranker from application settings, or None if disabled.

    Reads RERANKER_ENABLED, RERANKER_MODEL, and RERANKER_RELEVANCE_THRESHOLD
    from the environment (via core.config.settings). Uses the existing OpenAI/
    OpenRouter credentials for the API call.
    """
    from core.config import settings

    if not settings.reranker_enabled:
        return None

    api_key = settings.openrouter_api_key or settings.openai_api_key
    base_url = settings.openrouter_base_url

    config = RerankerConfig(
        api_key=api_key,
        base_url=base_url,
        model=settings.reranker_model,
        relevance_threshold=settings.reranker_relevance_threshold,
    )
    return ChunkReranker(config)
