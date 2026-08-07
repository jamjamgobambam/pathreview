import hashlib
from dataclasses import dataclass

import structlog
from sqlalchemy import select

from core.models.ingested_source import IngestedSource

from .chunking.strategy_selector import StrategySelector
from .embeddings.batch_processor import BatchEmbeddingProcessor
from .embeddings.provider import EmbeddingProvider
from .parsers.readme_parser import ReadmeParser
from .parsers.repo_analyzer import RepoAnalyzer
from .parsers.resume_parser import ResumeParser

logger = structlog.get_logger()


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
        vector_db,
        db_session,
        embedding_provider: EmbeddingProvider,
    ):
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
        content_hash = self._hash_content(content)
        source_id = f"resume_{profile_id}_{content_hash[:16]}"

        logger.info(
            "Starting resume ingestion",
            profile_id=profile_id,
            filename=filename,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = await self._check_skip(source_id)
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
        content_hash = self._hash_content(content)
        source_id = f"readme_{profile_id}_{repo_name}_{content_hash[:16]}"

        logger.info(
            "Starting README ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = await self._check_skip(source_id)
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
                filename=repo_name,
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
        repo_data: dict,
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
        content_hash = self._hash_content(str(repo_data))
        source_id = f"repo_{profile_id}_{repo_name}_{content_hash[:16]}"

        logger.info(
            "Starting repo metadata ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = await self._check_skip(source_id)
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
                filename=repo_name,
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

    def _hash_content(self, content: str | bytes) -> str:
        """Generate a SHA256 hash of content for deduplication."""
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()

    async def _check_skip(self, source_id: str) -> IngestResult | None:
        """
        Check if a source with this exact identity + content hash was already ingested.

        source_id already encodes profile/type/name and the content hash, so an
        exact match means the content is byte-identical to a prior submission.

        Returns IngestResult if should skip, None if should proceed.
        """
        try:
            result = await self.db_session.execute(
                select(IngestedSource).where(IngestedSource.source_id == source_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info("Source unchanged since last ingestion, skipping", source_id=source_id)
                return IngestResult(
                    source_id=source_id,
                    chunk_count=0,
                    skipped=True,
                    skip_reason="Content unchanged since last ingestion",
                )
        except Exception as e:
            logger.warning(
                "Could not check if source already ingested",
                source_id=source_id,
                error=str(e),
            )

        return None

    async def _record_ingested_source(
        self,
        source_id: str,
        source_type: str,
        profile_id: str,
        chunk_count: int,
        content_hash: str,
        filename: str | None = None,
        source_url: str | None = None,
    ) -> None:
        """
        Record that a source has been ingested, so future resubmissions of the
        same content can be detected and skipped.

        Args:
            source_id: Unique ID for the source (identity + content hash)
            source_type: Type of source (resume, readme, repo)
            profile_id: ID of profile owner
            chunk_count: Number of chunks created
            content_hash: Full SHA256 hash of the ingested content
            filename: Original filename or repo name, if applicable
            source_url: Source URL, if applicable
        """
        try:
            self.db_session.add(
                IngestedSource(
                    source_id=source_id,
                    profile_id=profile_id,
                    source_type=source_type,
                    source_url=source_url,
                    filename=filename,
                    content_hash=content_hash,
                    chunk_count=chunk_count,
                )
            )
            await self.db_session.commit()
            logger.info(
                "Recorded ingested source",
                source_id=source_id,
                source_type=source_type,
                profile_id=profile_id,
                chunk_count=chunk_count,
            )
        except Exception as e:
            logger.error(
                "Failed to record ingested source",
                source_id=source_id,
                error=str(e),
            )
