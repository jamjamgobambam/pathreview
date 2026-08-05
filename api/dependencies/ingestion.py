"""Factory and background task helpers for portfolio ingestion."""

from functools import lru_cache

import structlog

from core.config import settings
from ingestion.embeddings.provider import get_embedding_provider
from ingestion.pipeline import IngestionPipeline
from rag.retriever.vector_store import VectorStore

log = structlog.get_logger()


@lru_cache(maxsize=1)
def build_ingestion_pipeline() -> IngestionPipeline:
    """
    Construct (once) an IngestionPipeline from application settings.

    Cached so the ChromaDB client and embedding provider are reused across
    requests rather than rebuilt on every ingestion. Uses the configured
    embedding provider and a ChromaDB collection from the persistent vector
    store.
    """
    vector_store = VectorStore(persist_dir=settings.chroma_persist_dir)
    collection = vector_store.get_collection(settings.vector_collection_name)
    embedding_provider = get_embedding_provider(settings.embedding_provider)

    return IngestionPipeline(
        vector_db=collection,
        db_session=None,
        embedding_provider=embedding_provider,
    )


def run_portfolio_ingestion(profile_id: str, url: str) -> None:
    """
    Fetch, parse, and ingest a portfolio URL.

    Intended to run as a FastAPI BackgroundTask. Failures are logged rather than
    raised so they never affect the originating request/response.
    """
    try:
        pipeline = build_ingestion_pipeline()
        result = pipeline.ingest_portfolio(profile_id=profile_id, url=url)
        log.info(
            "portfolio_ingestion_completed",
            profile_id=profile_id,
            url=url,
            chunk_count=result.chunk_count,
            skipped=result.skipped,
        )
    except Exception as exc:
        log.error(
            "portfolio_ingestion_failed",
            profile_id=profile_id,
            url=url,
            error=str(exc),
        )
