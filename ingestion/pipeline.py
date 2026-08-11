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
        content_hash = self._hash_content(content)
        document_id = f"resume_{profile_id}"
        source_id = f"{document_id}_{content_hash}"

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
                "document_id": document_id,
                "profile_id": profile_id,
                "filename": filename,
                "source_type": "resume",
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Resume chunked successfully", chunk_count=len(chunks))

            # Evict any prior version of this document before storing the new one
            self._delete_existing_chunks(document_id)

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
        content_hash = self._hash_content(content)
        document_id = f"readme_{profile_id}_{repo_name}"
        source_id = f"{document_id}_{content_hash}"

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
            metadata.update({
                "source_id": source_id,
                "document_id": document_id,
                "profile_id": profile_id,
                "repo_name": repo_name,
                "source_type": "readme",
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("README chunked successfully", chunk_count=len(chunks))

            # Evict any prior version of this README before storing the new one
            self._delete_existing_chunks(document_id)

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
        content_hash = self._hash_content(str(repo_data))
        document_id = f"repo_{profile_id}_{repo_name}"
        source_id = f"{document_id}_{content_hash}"

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
                "document_id": document_id,
                "profile_id": profile_id,
                "source_type": "repo",
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Repository metadata chunked successfully", chunk_count=len(chunks))

            # Evict any prior version of this repo metadata before storing the new one
            self._delete_existing_chunks(document_id)

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

    def _check_skip(self, source_id: str, source_type: str) -> Optional[IngestResult]:
        """
        Check if this exact content has already been ingested.

        The vector store is the source of truth: ``source_id`` embeds the content
        hash, so if chunks with this id already exist the content is unchanged and
        we skip re-embedding it. A changed document has a different ``source_id``
        and is not skipped here — its stale chunks are evicted by
        ``_delete_existing_chunks`` before the new version is stored.

        Args:
            source_id: Content-addressed id for this exact version of the source.
            source_type: Type of source (resume, readme, repo).

        Returns:
            IngestResult if ingestion should be skipped, None if it should proceed.
        """
        try:
            existing = self.vector_db.get(where={"source_id": {"$eq": source_id}}, limit=1)
            if existing and existing.get("ids"):
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

    def _delete_existing_chunks(self, document_id: str) -> None:
        """
        Remove any previously stored chunks for a document before re-ingesting.

        Chunks are keyed on a stable ``document_id`` (independent of content), so
        an edited document fully replaces its prior version instead of piling new
        chunks alongside the old ones. This prevents the retriever from returning
        stale content after a re-ingestion (issue #27). Safe no-op when the
        document has never been ingested.

        Args:
            document_id: Stable identifier for the document, independent of its
                content hash (e.g. ``readme_{profile_id}_{repo_name}``).
        """
        try:
            existing = self.vector_db.get(where={"document_id": {"$eq": document_id}})
            stale_ids = existing.get("ids") if existing else None
            if stale_ids:
                self.vector_db.delete(ids=stale_ids)
                logger.info(
                    "Evicted stale chunks before re-ingestion",
                    document_id=document_id,
                    count=len(stale_ids),
                )
        except Exception as e:
            logger.warning(
                "Could not delete existing chunks",
                document_id=document_id,
                error=str(e),
            )

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
