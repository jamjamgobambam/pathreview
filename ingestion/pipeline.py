import hashlib
import json
from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.ingested_source import IngestedSource

from .chunking.strategy_selector import StrategySelector
from .embeddings.batch_processor import BatchEmbeddingProcessor
from .embeddings.provider import EmbeddingProvider
from .parsers.readme_parser import ReadmeParser
from .parsers.repo_analyzer import RepoAnalyzer
from .parsers.resume_parser import ResumeParser

logger = structlog.get_logger()

REPO_DEDUP_FIELDS = (
    "name",
    "description",
    "language",
    "languages",
    "topics",
    "html_url",
    "file_structure",
)


def _is_unique_violation(error: IntegrityError) -> bool:
    """Return whether an integrity error is a duplicate-key violation."""
    original_error = getattr(error, "orig", None)
    sqlstate = getattr(original_error, "sqlstate", None) or getattr(
        original_error,
        "pgcode",
        None,
    )

    if sqlstate is not None:
        return str(sqlstate) == "23505"

    return "unique" in type(original_error).__name__.lower()


@dataclass
class IngestResult:
    """Result of ingesting a source."""

    source_id: str
    chunk_count: int
    skipped: bool
    skip_reason: str | None = None


class IngestionPipeline:
    """Main orchestration for document ingestion and embedding."""

    def __init__(
        self,
        vector_db: Any,
        db_session: AsyncSession,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        """
        Initialize the ingestion pipeline.

        Args:
            vector_db: ChromaDB collection for storing embeddings
            db_session: Database session for storing metadata
            embedding_provider: EmbeddingProvider for generating embeddings
        """
        self.vector_db = vector_db
        self.db_session = db_session
        self.embedding_provider = embedding_provider
        self.strategy_selector = StrategySelector()
        self.batch_processor = BatchEmbeddingProcessor(embedding_provider, vector_db)

        # Initialize parsers
        self.resume_parser = ResumeParser()
        self.readme_parser = ReadmeParser()
        self.repo_analyzer = RepoAnalyzer()

    async def ingest_resume(
        self,
        profile_id: str,
        content: str | bytes,
        filename: str,
    ) -> IngestResult:
        """
        Ingest a resume document.

        Args:
            profile_id: ID of the profile owner
            content: Resume content (PDF bytes or markdown string)
            filename: Original filename

        Returns:
            IngestResult with ingestion status
        """
        content_hash = self._content_digest(content)
        source_id = f"resume_{profile_id}_{content_hash[:16]}"

        logger.info(
            "Starting resume ingestion",
            profile_id=profile_id,
            filename=filename,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = await self._check_skip(source_id, "resume")
        if skip_result:
            return skip_result

        try:
            # Parse resume
            parse_result = self.resume_parser.parse(content)
            logger.info(
                "Resume parsed successfully",
                sections=parse_result.metadata.get("detected_sections"),
            )

            # Prepare metadata
            metadata = parse_result.metadata.copy()
            metadata.update(
                {
                    "source_id": source_id,
                    "profile_id": profile_id,
                    "filename": filename,
                    "source_type": "resume",
                }
            )

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Resume chunked successfully", chunk_count=len(chunks))

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("Resume embeddings stored", chunk_count=len(chunks))

            # Record in database
            await self._record_ingested_source(
                source_id=source_id,
                source_type="resume",
                profile_id=profile_id,
                chunk_count=len(chunks),
                content_hash=content_hash,
                filename=filename,
            )

            return IngestResult(
                source_id=source_id,
                chunk_count=len(chunks),
                skipped=False,
            )

        except Exception as e:
            logger.error(
                "Resume ingestion failed",
                profile_id=profile_id,
                filename=filename,
                error=str(e),
            )
            raise

    async def ingest_readme(
        self,
        profile_id: str,
        repo_name: str,
        content: str | bytes,
    ) -> IngestResult:
        """
        Ingest a README document.

        Args:
            profile_id: ID of the profile owner
            repo_name: Name of the repository
            content: README content (markdown string or bytes)

        Returns:
            IngestResult with ingestion status
        """
        content_hash = self._content_digest(content)
        source_id = f"readme_{profile_id}_{repo_name}_{content_hash[:16]}"

        logger.info(
            "Starting README ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = await self._check_skip(source_id, "readme")
        if skip_result:
            return skip_result

        try:
            # Parse README
            parse_result = self.readme_parser.parse(content)
            logger.info(
                "README parsed successfully",
                heading_count=parse_result.metadata.get("heading_count"),
                word_count=parse_result.metadata.get("word_count"),
            )

            # Prepare metadata
            metadata = parse_result.metadata.copy()
            metadata.update(
                {
                    "source_id": source_id,
                    "profile_id": profile_id,
                    "repo_name": repo_name,
                    "source_type": "readme",
                }
            )

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("README chunked successfully", chunk_count=len(chunks))

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("README embeddings stored", chunk_count=len(chunks))

            # Record in database
            await self._record_ingested_source(
                source_id=source_id,
                source_type="readme",
                profile_id=profile_id,
                chunk_count=len(chunks),
                content_hash=content_hash,
            )

            return IngestResult(
                source_id=source_id,
                chunk_count=len(chunks),
                skipped=False,
            )

        except Exception as e:
            logger.error(
                "README ingestion failed",
                profile_id=profile_id,
                repo_name=repo_name,
                error=str(e),
            )
            raise

    async def ingest_repo_metadata(
        self,
        profile_id: str,
        repo_data: dict[str, Any],
    ) -> IngestResult:
        """
        Ingest repository metadata.

        Args:
            profile_id: ID of the profile owner
            repo_data: Repository metadata dictionary

        Returns:
            IngestResult with ingestion status
        """
        repo_name = repo_data.get("name", "unknown")
        content_hash = self._content_digest(self._repo_dedup_payload(repo_data))
        source_id = f"repo_{profile_id}_{repo_name}_{content_hash[:16]}"

        logger.info(
            "Starting repo metadata ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = await self._check_skip(source_id, "repo")
        if skip_result:
            return skip_result

        try:
            # Analyze repository
            parse_result = self.repo_analyzer.parse(repo_data)
            logger.info(
                "Repository analyzed successfully",
                language=parse_result.metadata.get("primary_language"),
                tech_stack=parse_result.metadata.get("tech_stack"),
            )

            # Prepare metadata
            metadata = parse_result.metadata.copy()
            metadata.update(
                {
                    "source_id": source_id,
                    "profile_id": profile_id,
                    "source_type": "repo",
                }
            )

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Repository metadata chunked successfully", chunk_count=len(chunks))

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("Repository embeddings stored", chunk_count=len(chunks))

            # Record in database
            await self._record_ingested_source(
                source_id=source_id,
                source_type="repo",
                profile_id=profile_id,
                chunk_count=len(chunks),
                content_hash=content_hash,
                source_url=repo_data.get("html_url"),
            )

            return IngestResult(
                source_id=source_id,
                chunk_count=len(chunks),
                skipped=False,
            )

        except Exception as e:
            logger.error(
                "Repository ingestion failed",
                profile_id=profile_id,
                repo_name=repo_name,
                error=str(e),
            )
            raise

    def _content_digest(self, content: str | bytes) -> str:
        """Generate the full SHA-256 hexadecimal digest of content."""
        if isinstance(content, str):
            content = content.encode("utf-8")

        return hashlib.sha256(content).hexdigest()

    def _hash_content(self, content: str | bytes) -> str:
        """Generate the shortened digest used inside vector source identifiers."""
        return self._content_digest(content)[:16]

    def _repo_dedup_payload(self, repo_data: dict[str, Any]) -> str:
        """Build stable repository content for deduplication."""
        stable_data = {
            field: repo_data.get(field) for field in REPO_DEDUP_FIELDS if field in repo_data
        }
        stable_data["has_readme"] = bool(repo_data.get("readme_content"))

        return json.dumps(
            stable_data,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    async def _check_skip(
        self,
        source_id: str,
        source_type: str,
    ) -> IngestResult | None:
        """Return a skipped result when the source already exists."""
        try:
            result = await self.db_session.execute(
                select(IngestedSource).where(
                    IngestedSource.source_id == source_id,
                )
            )
            existing_source = result.scalar_one_or_none()
        except SQLAlchemyError as error:
            logger.error(
                "Could not check ingestion state",
                source_id=source_id,
                source_type=source_type,
                error=str(error),
            )
            raise

        if existing_source is None:
            return None

        logger.info(
            "Source already ingested, skipping",
            source_id=source_id,
            source_type=source_type,
        )

        return IngestResult(
            source_id=source_id,
            chunk_count=0,
            skipped=True,
            skip_reason="Source already ingested",
        )

    async def _record_ingested_source(
        self,
        source_id: str,
        source_type: str,
        profile_id: str,
        chunk_count: int,
        *,
        content_hash: str | None = None,
        filename: str | None = None,
        source_url: str | None = None,
    ) -> None:
        """Persist successful ingestion bookkeeping."""
        record = IngestedSource(
            profile_id=profile_id,
            source_type=source_type,
            source_id=source_id,
            content_hash=content_hash,
            filename=filename,
            source_url=source_url,
            chunk_count=chunk_count,
        )

        try:
            self.db_session.add(record)
            await self.db_session.commit()
        except IntegrityError as error:
            await self.db_session.rollback()

            if _is_unique_violation(error):
                logger.info(
                    "Source was recorded by a concurrent ingestion",
                    source_id=source_id,
                    source_type=source_type,
                )
                return

            logger.error(
                "Failed to record ingested source",
                source_id=source_id,
                error=str(error),
            )
            raise
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            logger.error(
                "Failed to record ingested source",
                source_id=source_id,
                error=str(error),
            )
            raise

        logger.info(
            "Recorded ingested source",
            source_id=source_id,
            source_type=source_type,
            profile_id=profile_id,
            chunk_count=chunk_count,
        )
