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
from .parsers.web_parser import WebParser


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
        self.web_parser = WebParser()

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
        source_id = f"resume_{profile_id}_{content_hash}"

        logger.info(
            "Starting resume ingestion",
            profile_id=profile_id,
            filename=filename,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(profile_id, "resume", content_hash)
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
            self._record_ingested_source(
                profile_id, "resume", content_hash, len(chunks), filename=filename
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
        source_id = f"readme_{profile_id}_{repo_name}_{content_hash}"

        logger.info(
            "Starting README ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(profile_id, "readme", content_hash)
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
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("README chunked successfully", chunk_count=len(chunks))

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("README embeddings stored", chunk_count=len(chunks))

            # Record in database
            self._record_ingested_source(
                profile_id, "readme", content_hash, len(chunks), filename=repo_name
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
        source_id = f"repo_{profile_id}_{repo_name}_{content_hash}"

        logger.info(
            "Starting repo metadata ingestion",
            profile_id=profile_id,
            repo_name=repo_name,
            source_id=source_id,
        )

        # Check if already ingested
        skip_result = self._check_skip(profile_id, "repo", content_hash)
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
            self._record_ingested_source(
                profile_id,
                "repo",
                content_hash,
                len(chunks),
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

    def ingest_portfolio(
        self,
        profile_id: str,
        url: str,
    ) -> IngestResult:
        """
        Ingest a portfolio website.

        Args:
            profile_id: ID of the profile owner
            url: Portfolio URL to fetch and ingest

        Returns:
            IngestResult with ingestion status
        """
        logger.info("Starting portfolio ingestion", profile_id=profile_id, url=url)

        try:
            # Fetch the page
            html = self.web_parser.fetch(url)

            content_hash = self._hash_content(html)
            source_id = f"web_{profile_id}_{content_hash}"

            # Check if already ingested
            skip_result = self._check_skip(profile_id, "web", content_hash)
            if skip_result:
                return skip_result

            # Parse portfolio page
            parse_result = self.web_parser.parse(html)
            logger.info(
                "Portfolio parsed successfully",
                word_count=parse_result.metadata.get("word_count"),
            )

            # Prepare metadata
            metadata = parse_result.metadata.copy()
            metadata.update({
                "source_id": source_id,
                "profile_id": profile_id,
                "source_url": url,
                "source_type": "web",
            })

            # Chunk the content
            chunks = self.strategy_selector.chunk(parse_result.text, metadata)
            logger.info("Portfolio chunked successfully", chunk_count=len(chunks))

            # Generate embeddings and store
            self.batch_processor.process(chunks)
            logger.info("Portfolio embeddings stored", chunk_count=len(chunks))

            # Record in database
            self._record_ingested_source(
                profile_id, "web", content_hash, len(chunks), source_url=url
            )

            return IngestResult(
                source_id=source_id,
                chunk_count=len(chunks),
                skipped=False,
            )

        except Exception as e:
            logger.error(
                "Portfolio ingestion failed",
                profile_id=profile_id,
                url=url,
                error=str(e),
            )
            raise

    def _hash_content(self, content: str | bytes) -> str:
        """Generate a hash of content for deduplication."""
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def _check_skip(
        self,
        profile_id: str,
        source_type: str,
        content_hash: str,
    ) -> Optional[IngestResult]:
        """
        Check if this exact content was already ingested for this profile.

        Returns IngestResult if should skip, None if should proceed.
        """
        try:
            existing = (
                self.db_session.query(IngestedSource)
                .filter_by(
                    profile_id=profile_id,
                    source_type=source_type,
                    content_hash=content_hash,
                )
                .first()
            )

            if existing:
                logger.info(
                    "Source already ingested, skipping",
                    profile_id=profile_id,
                    source_type=source_type,
                    content_hash=content_hash,
                )
                return IngestResult(
                    source_id=str(existing.id),
                    chunk_count=existing.chunk_count,
                    skipped=True,
                    skip_reason="Source already ingested",
                )
        except Exception as e:
            logger.warning(
                "Could not check if source already ingested",
                profile_id=profile_id,
                source_type=source_type,
                error=str(e),
            )

        return None

    def _record_ingested_source(
        self,
        profile_id: str,
        source_type: str,
        content_hash: str,
        chunk_count: int,
        filename: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> None:
        """
        Persist a record of an ingested source so future ingestion can dedup against it.

        Args:
            profile_id: ID of profile owner
            source_type: Type of source (resume, readme, repo, web)
            content_hash: SHA256 hash of the ingested content
            chunk_count: Number of chunks created
            filename: Original filename, if applicable (e.g. resume)
            source_url: Source URL, if applicable (e.g. repo, web)
        """
        try:
            record = IngestedSource(
                profile_id=profile_id,
                source_type=source_type,
                source_url=source_url,
                filename=filename,
                content_hash=content_hash,
                chunk_count=chunk_count,
            )
            self.db_session.add(record)
            self.db_session.commit()
            logger.info(
                "Recorded ingested source",
                profile_id=profile_id,
                source_type=source_type,
                chunk_count=chunk_count,
            )
        except Exception as e:
            logger.error(
                "Failed to record ingested source",
                profile_id=profile_id,
                source_type=source_type,
                error=str(e),
            )
            self.db_session.rollback()
