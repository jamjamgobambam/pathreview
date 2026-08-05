import hashlib
from dataclasses import dataclass
from typing import Optional

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
        source_id = f"resume_{profile_id}"

        logger.info(
            "Starting resume ingestion",
            profile_id=profile_id,
            filename=filename,
            source_id=source_id,
            content_hash=content_hash,
        )

        # Skip only if this exact content was already ingested
        skip_result = self._check_skip(source_id, "resume", content_hash)
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
                "content_hash": content_hash,
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Resume chunked successfully", chunk_count=len(chunks))

            # Remove any previous version's chunks before writing new ones so
            # re-ingestion replaces rather than accumulates (see issue #27).
            self._delete_existing_chunks(source_id)

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("Resume embeddings stored", chunk_count=len(chunks))

            # Record in database
            self._record_ingested_source(
                source_id, "resume", profile_id, len(chunks), content_hash
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
        source_id = f"readme_{profile_id}_{repo_name}"

        logger.info(
            "Starting README ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
            content_hash=content_hash,
        )

        # Skip only if this exact content was already ingested
        skip_result = self._check_skip(source_id, "readme", content_hash)
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
                "profile_id": profile_id,
                "repo_name": repo_name,
                "source_type": "readme",
                "content_hash": content_hash,
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("README chunked successfully", chunk_count=len(chunks))

            # Remove any previous version's chunks before writing new ones so
            # re-ingestion replaces rather than accumulates (see issue #27).
            self._delete_existing_chunks(source_id)

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("README embeddings stored", chunk_count=len(chunks))

            # Record in database
            self._record_ingested_source(
                source_id, "readme", profile_id, len(chunks), content_hash
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
        source_id = f"repo_{profile_id}_{repo_name}"

        logger.info(
            "Starting repo metadata ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
            content_hash=content_hash,
        )

        # Skip only if this exact content was already ingested
        skip_result = self._check_skip(source_id, "repo", content_hash)
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
                "content_hash": content_hash,
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Repository metadata chunked successfully", chunk_count=len(chunks))

            # Remove any previous version's chunks before writing new ones so
            # re-ingestion replaces rather than accumulates (see issue #27).
            self._delete_existing_chunks(source_id)

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("Repository embeddings stored", chunk_count=len(chunks))

            # Record in database
            self._record_ingested_source(
                source_id, "repo", profile_id, len(chunks), content_hash
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
        """Generate a hash of content, used as a source's version marker."""
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def _delete_existing_chunks(self, source_id: str) -> None:
        """Delete a source's previously stored chunks before re-ingesting it.

        Chunks are keyed on the source's stable ``source_id`` (not its content
        hash), so deleting by that id removes the prior version's chunks —
        including when the new version produces fewer chunks — instead of
        leaving stale embeddings behind (issue #27). Best-effort: a failure here
        is logged rather than raised so a transient vector-store error does not
        abort ingestion.

        Args:
            source_id: Stable identifier of the source whose chunks to remove.
        """
        try:
            self.vector_db.delete(where={"source_id": {"$eq": source_id}})
        except Exception as e:
            logger.warning(
                "Could not delete existing chunks before re-ingestion",
                source_id=source_id,
                error=str(e),
            )

    def _check_skip(
        self, source_id: str, source_type: str, content_hash: str
    ) -> Optional[IngestResult]:
        """
        Check whether this exact content has already been ingested.

        Deduplication is keyed on ``content_hash``: identical content is a
        no-op, but edited content produces a new hash and proceeds — after which
        ``_delete_existing_chunks`` replaces the prior version's chunks. This is
        why a stable ``source_id`` no longer causes edited documents to be
        wrongly skipped.

        Args:
            source_id: Stable identifier of the source (for logging).
            source_type: Type of source (resume, readme, repo).
            content_hash: Hash of the current content, used as the version key.

        Returns:
            IngestResult if ingestion should be skipped, otherwise None.
        """
        try:
            existing = (
                self.db_session.query(IngestedSource)
                .filter_by(content_hash=content_hash)
                .first()
            )

            if existing:
                logger.info(
                    "Source content already ingested, skipping",
                    source_id=source_id,
                    content_hash=content_hash,
                )
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
        content_hash: str,
    ) -> None:
        """
        Record that a source has been ingested at a given content version.

        Note: the ``IngestedSource`` model has no ``source_id`` column, so
        durable persistence of the stable id is deferred to a follow-up that
        adds one. This records the ingestion (including ``content_hash``, the
        key ``_check_skip`` reads) as structured log output for now.

        Args:
            source_id: Stable ID for the source.
            source_type: Type of source (resume, readme, repo).
            profile_id: ID of profile owner.
            chunk_count: Number of chunks created.
            content_hash: Hash of the ingested content (version marker).
        """
        try:
            logger.info(
                "Recording ingested source",
                source_id=source_id,
                source_type=source_type,
                profile_id=profile_id,
                chunk_count=chunk_count,
                content_hash=content_hash,
            )
        except Exception as e:
            logger.error(
                "Failed to record ingested source",
                source_id=source_id,
                error=str(e),
            )
