import hashlib
from dataclasses import dataclass
from typing import Optional

import structlog

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
    skip_reason: Optional[str] = None


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
            logger.info("Resume parsed successfully", sections=parse_result.metadata.get("detected_sections"))

            # Prepare metadata
            metadata = parse_result.metadata.copy()
            metadata.update({
                "source_id": source_id,
                "profile_id": profile_id,
                "filename": filename,
                "source_type": "resume",
            })

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

        Re-ingestion is version-aware: a README is identified by a stable
        source_id (profile + repo), while content_hash records the revision. If
        the content is unchanged since the last ingestion it is skipped; if it
        changed, the previous version's chunks are removed before the new ones
        are stored, so stale content is never left behind.

        Args:
            profile_id: ID of the profile owner
            repo_name: Name of the repository
            content: README content (markdown string or bytes)

        Returns:
            IngestResult with ingestion status
        """
        # Split identity from version: source_id is a stable logical key for this
        # README (constant across edits), while content_hash stamps the revision.
        source_id = f"readme_{profile_id}_{repo_name}"
        content_hash = self._hash_content(content)

        logger.info(
            "Starting README ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Skip only if this exact content was already ingested. Otherwise fall
        # through so an edited README replaces its stale chunks (deleted below).
        if self._existing_content_hash(source_id) == content_hash:
            logger.info(
                "README unchanged since last ingestion, skipping",
                source_id=source_id,
            )
            return IngestResult(
                source_id=source_id,
                chunk_count=0,
                skipped=True,
                skip_reason="Content unchanged since last ingestion",
            )

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
            metadata.update({
                "source_id": source_id,
                "content_hash": content_hash,
                "profile_id": profile_id,
                "repo_name": repo_name,
                "source_type": "readme",
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("README chunked successfully", chunk_count=len(chunks))

            # Replace any prior version: clear its chunks before storing the new
            # ones so stale content can no longer be retrieved. Guard on chunks so
            # an empty parse can't wipe a good previously ingested version.
            if chunks:
                self.vector_db.delete(where={"source_id": source_id})
                logger.info("Cleared previous README version", source_id=source_id)

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
        source_id = f"repo_{profile_id}_{repo_name}_{self._hash_content(str(repo_data))}"

        logger.info(
            "Starting repo metadata ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(source_id, "repo")
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
            metadata.update({
                "source_id": source_id,
                "profile_id": profile_id,
                "source_type": "repo",
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Repository metadata chunked successfully", chunk_count=len(chunks))

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("Repository embeddings stored", chunk_count=len(chunks))

            # Record in database
            self._record_ingested_source(source_id, "repo", profile_id, len(chunks))

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
        """Generate a hash of content for deduplication."""
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def _existing_content_hash(self, source_id: str) -> str | None:
        """Return the content_hash of a previously ingested source, or None.

        Reads stored chunk metadata for this source_id straight from the vector
        store, which is the source of truth for what has already been ingested.
        Used to decide whether re-ingested content is unchanged (skip) or edited
        (replace).

        Args:
            source_id: Stable logical identifier for the source.

        Returns:
            The stored content_hash, or None if this source has no chunks yet.
        """
        try:
            existing = self.vector_db.get(where={"source_id": source_id})
        except Exception as e:
            logger.warning(
                "Could not look up existing source",
                source_id=source_id,
                error=str(e),
            )
            return None

        metadatas = existing.get("metadatas") or []
        if not metadatas:
            return None
        return metadatas[0].get("content_hash")

    def _check_skip(self, source_id: str, source_type: str) -> Optional[IngestResult]:
        """
        Check if source has already been ingested.

        Returns IngestResult if should skip, None if should proceed.
        """
        try:
            # Query database for existing source
            # This assumes a table/model named IngestedSource
            existing = self.db_session.query(
                "IngestedSource"  # Placeholder - actual query depends on ORM
            ).filter_by(source_id=source_id).first()

            if existing:
                logger.info("Source already ingested, skipping", source_id=source_id)
                return IngestResult(
                    source_id=source_id,
                    chunk_count=0,
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
    ) -> None:
        """
        Record that a source has been ingested.

        Args:
            source_id: Unique ID for the source
            source_type: Type of source (resume, readme, repo)
            profile_id: ID of profile owner
            chunk_count: Number of chunks created
        """
        try:
            # This is a placeholder for actual database recording
            # In a real implementation, would create IngestedSource record
            logger.info(
                "Recording ingested source",
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
