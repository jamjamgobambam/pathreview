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


@dataclass
class IngestResult:
    """Result of ingesting a source."""

    source_id: str
    chunk_count: int
    skipped: bool
    skip_reason: str | None = None


# Fields of a GitHub repo payload that identify *what the repo is*, as opposed to
# how it is currently doing. Everything outside this set (stargazers_count,
# forks_count, open_issues_count, pushed_at, ...) changes between routine fetches
# of an unchanged repository and must not affect the dedup key.
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
    """
    True when an IntegrityError is a duplicate-key violation (SQLSTATE 23505).

    Distinguishes the benign concurrent-ingest race from genuine integrity
    failures such as a foreign-key violation on an unknown profile_id.
    """
    orig = getattr(error, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if sqlstate is not None:
        return str(sqlstate) == "23505"
    return "unique" in type(orig).__name__.lower()


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
            db_session: AsyncSession for storing ingestion bookkeeping
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
                source_id,
                "resume",
                profile_id,
                len(chunks),
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
                source_id,
                "readme",
                profile_id,
                len(chunks),
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
                source_id,
                "repo",
                profile_id,
                len(chunks),
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
        """Generate the full SHA-256 hex digest of content."""
        if isinstance(content, str):
            content = content.encode()
        return hashlib.sha256(content).hexdigest()

    def _hash_content(self, content: str | bytes) -> str:
        """Generate a short content hash, as embedded in source_id."""
        return self._content_digest(content)[:16]

    def _repo_dedup_payload(self, repo_data: dict) -> str:
        """
        Build a canonical, stable string identifying a repository.

        Only REPO_DEDUP_FIELDS participate, serialized with sorted keys, so that
        routine re-fetches of an unchanged repo (new star count, new pushed_at,
        different key order) produce a byte-identical payload — and therefore the
        same source_id. A genuine edit to the description, topics, or file layout
        still changes the payload and triggers a full re-ingestion.

        Note: RepoAnalyzer's generated text also embeds volatile stats (Stars,
        Forks, Open Issues), so a skipped re-ingest leaves those stale in the
        stored chunk. That is deliberate — refreshing stats is a re-ingestion
        policy question, tracked separately from this deduplication fix.
        """
        stable = {field: repo_data.get(field) for field in REPO_DEDUP_FIELDS if field in repo_data}
        # has_readme feeds the generated text as a boolean; the README body itself
        # is deduplicated independently via ingest_readme().
        stable["has_readme"] = bool(repo_data.get("readme_content"))
        return json.dumps(stable, sort_keys=True, default=str)

    async def _check_skip(self, source_id: str, source_type: str) -> IngestResult | None:
        """
        Check if source has already been ingested.

        Returns IngestResult if should skip, None if should proceed.

        On database failure we proceed with ingestion — availability beats
        deduplication — but log at error level so the failure is visible rather
        than silently disabling the skip check.

        Only SQLAlchemyError is caught, deliberately. The original bug was an
        AttributeError (calling the sync .query() API on an AsyncSession) that a
        bare `except Exception` swallowed, turning a broken query into a silent
        no-op. Narrowing to database errors means an unavailable database still
        degrades gracefully, while a programming error in this query fails loudly
        instead of quietly re-introducing issue #6.
        """
        try:
            result = await self.db_session.execute(
                select(IngestedSource).where(IngestedSource.source_id == source_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
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
        except SQLAlchemyError as e:
            logger.error(
                "Could not check if source already ingested; proceeding with ingestion",
                source_id=source_id,
                source_type=source_type,
                error=str(e),
            )

        return None

    async def _record_ingested_source(
        self,
        source_id: str,
        source_type: str,
        profile_id: str,
        chunk_count: int,
        content_hash: str | None = None,
        filename: str | None = None,
        source_url: str | None = None,
    ) -> None:
        """
        Record that a source has been ingested.

        Args:
            source_id: Unique dedup key for the source
            source_type: Type of source (resume, readme, repo)
            profile_id: ID of profile owner
            chunk_count: Number of chunks created
            content_hash: Full SHA-256 digest of the deduplicated content
            filename: Original filename, when the source had one
            source_url: Origin URL, when the source had one
        """
        record = IngestedSource(
            profile_id=profile_id,
            source_type=source_type,
            source_id=source_id,
            content_hash=content_hash,
            chunk_count=chunk_count,
            filename=filename,
            source_url=source_url,
        )

        try:
            self.db_session.add(record)
            await self.db_session.commit()
            logger.info(
                "Recorded ingested source",
                source_id=source_id,
                source_type=source_type,
                profile_id=profile_id,
                chunk_count=chunk_count,
            )
        except IntegrityError as e:
            await self.db_session.rollback()
            if _is_unique_violation(e):
                # Another worker recorded this same source between our _check_skip()
                # and this commit. The unique constraint did its job; treat the row
                # as present rather than failing an otherwise successful ingestion.
                logger.info(
                    "Source already recorded by a concurrent ingest",
                    source_id=source_id,
                    source_type=source_type,
                )
            else:
                # e.g. a foreign-key violation from an unknown profile_id — a real
                # bug, not a benign race. Do not disguise it as deduplication.
                logger.error(
                    "Failed to record ingested source",
                    source_id=source_id,
                    error=str(e),
                )
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error(
                "Failed to record ingested source",
                source_id=source_id,
                error=str(e),
            )
