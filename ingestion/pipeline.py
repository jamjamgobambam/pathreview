import hashlib
import json
from dataclasses import dataclass

import structlog

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

    def ingest_resume(
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
        source_id = f"resume_{profile_id}_{self._hash_content(content)}"

        logger.info(
            "Starting resume ingestion",
            profile_id=profile_id,
            filename=filename,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(source_id, "resume")
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
            self._record_ingested_source(source_id, "resume", profile_id, len(chunks))

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

    def ingest_readme(
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
        source_id = f"readme_{profile_id}_{repo_name}_{self._hash_content(content)}"

        logger.info(
            "Starting README ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(source_id, "readme")
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
            self._record_ingested_source(source_id, "readme", profile_id, len(chunks))

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

    def ingest_repo_metadata(
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
        repo_content = self._serialize_repo_data(repo_data)
        content_hash = self._hash_content(repo_content)
        repo_url = repo_data.get("html_url") or None
        if repo_url is not None:
            repo_url = str(repo_url)
        source_id = f"repo_{profile_id}_{repo_name}_{content_hash}"

        logger.info(
            "Starting repo metadata ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(
            source_id,
            "repo",
            profile_id=profile_id,
            content_hash=content_hash,
            source_url=repo_url,
        )
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
            self._record_ingested_source(
                source_id,
                "repo",
                profile_id,
                len(chunks),
                content_hash=content_hash,
                source_url=repo_url,
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

    def _serialize_repo_data(self, repo_data: dict) -> str:
        """Serialize repository metadata deterministically for deduplication."""
        return json.dumps(repo_data, sort_keys=True, default=str)

    def _hash_content(self, content: str | bytes) -> str:
        """Generate a hash of content for deduplication."""
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def _check_skip(
        self,
        source_id: str,
        source_type: str,
        profile_id: str | None = None,
        content_hash: str | None = None,
        source_url: str | None = None,
    ) -> IngestResult | None:
        """
        Check if source has already been ingested.

        Returns IngestResult if should skip, None if should proceed.
        """
        if not content_hash and not source_url:
            logger.debug(
                "Skipping duplicate check without stable identifier",
                source_id=source_id,
                source_type=source_type,
            )
            return None

        try:
            filters = {"source_type": source_type}
            if profile_id is not None:
                filters["profile_id"] = profile_id
            if content_hash is not None:
                filters["content_hash"] = content_hash
            if source_url is not None:
                filters["source_url"] = source_url

            existing = self.db_session.query(IngestedSource).filter_by(**filters).first()

            if existing:
                logger.info("Source already ingested, skipping", source_id=source_id)
                return IngestResult(
                    source_id=source_id,
                    chunk_count=getattr(existing, "chunk_count", 0),
                    skipped=True,
                    skip_reason="Source already ingested",
                )
        except Exception as e:
            logger.warning(
                "Could not check if source already ingested",
                source_id=source_id,
                error=str(e),
            )

        return None

    def _record_ingested_source(
        self,
        source_id: str,
        source_type: str,
        profile_id: str,
        chunk_count: int,
        content_hash: str | None = None,
        source_url: str | None = None,
        filename: str | None = None,
    ) -> None:
        """
        Record that a source has been ingested.

        Args:
            source_id: Unique ID for the source
            source_type: Type of source (resume, readme, repo)
            profile_id: ID of profile owner
            chunk_count: Number of chunks created
            content_hash: Stable hash of the ingested source
            source_url: URL for URL-addressable sources
            filename: Filename for file-based sources
        """
        if not content_hash and not source_url:
            logger.info(
                "Skipping ingested source record without stable identifier",
                source_id=source_id,
                source_type=source_type,
                profile_id=profile_id,
                chunk_count=chunk_count,
            )
            return

        try:
            ingested_source = IngestedSource(
                profile_id=profile_id,
                source_type=source_type,
                source_url=source_url,
                filename=filename,
                content_hash=content_hash,
                chunk_count=chunk_count,
            )
            self.db_session.add(ingested_source)

            commit = getattr(self.db_session, "commit", None)
            if callable(commit):
                commit()

            logger.info(
                "Recording ingested source",
                source_id=source_id,
                source_type=source_type,
                profile_id=profile_id,
                chunk_count=chunk_count,
            )
        except Exception as e:
            rollback = getattr(self.db_session, "rollback", None)
            if callable(rollback):
                rollback()

            logger.error(
                "Failed to record ingested source",
                source_id=source_id,
                error=str(e),
            )
            raise
