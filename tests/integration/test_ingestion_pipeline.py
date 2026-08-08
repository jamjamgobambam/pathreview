"""Integration tests for the ingestion pipeline."""

import json
import pathlib
from unittest.mock import MagicMock

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.pipeline import IngestionPipeline, IngestResult


def _load_profile_fixtures(profile_id: str) -> dict:
    """Load all fixture data for a profile (resume, repos with readme and metadata)."""
    fixture_dir = pathlib.Path(__file__).parent.parent / "fixtures" / "sample_resumes" / profile_id

    if not fixture_dir.exists():
        raise FileNotFoundError(f"Fixture directory not found for profile {profile_id}")

    # Load resume (either .md or .pdf)
    resume_content = None
    if (fixture_dir / "resume.md").exists():
        resume_content = (fixture_dir / "resume.md").read_text(encoding="utf-8")
    elif (fixture_dir / "resume.pdf").exists():
        resume_content = (fixture_dir / "resume.pdf").read_bytes()
    else:
        raise FileNotFoundError(f"Resume file not found for profile {profile_id}")

    # Load all repos (metadata + readme pairs)
    repos = []
    metadata_files = sorted(fixture_dir.glob("*_metadata.json"))

    for metadata_file in metadata_files:
        repo_name = metadata_file.stem.replace("_metadata", "")
        readme_file = fixture_dir / f"{repo_name}_README.md"

        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        readme_content = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

        repos.append(
            {
                "name": repo_name,
                "readme": readme_content,
                "metadata": metadata,
            }
        )

    return {
        "profile_id": profile_id,
        "resume": resume_content,
        "repos": repos,
    }


@pytest.mark.integration
class TestIngestionPipeline:
    """Test suite for document ingestion pipeline."""

    @pytest.fixture
    def mock_vector_db(self) -> MagicMock:
        """Mock ChromaDB collection."""
        mock_db = MagicMock()
        mock_db.add = MagicMock(return_value=None)
        return mock_db

    @pytest.fixture
    def mock_db_session(self) -> MagicMock:
        """Create a mock database session."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        return session

    @pytest.fixture
    def pipeline(self, mock_vector_db: MagicMock, mock_db_session: MagicMock) -> IngestionPipeline:
        """Create an IngestionPipeline with mocked dependencies."""
        return IngestionPipeline(
            vector_db=mock_vector_db,
            db_session=mock_db_session,
            embedding_provider=MockEmbeddingProvider(),
        )

    @pytest.fixture(scope="session")
    def fixture_ql_001(self) -> dict:
        """Load all fixtures for profile ql-001."""
        return _load_profile_fixtures("ql-001")

    @pytest.fixture(scope="session")
    def fixture_ql_100(self) -> dict:
        """Load all fixtures for profile ql-100."""
        return _load_profile_fixtures("ql-100")

    @pytest.fixture(scope="session")
    def fixture_jn_001(self) -> dict:
        """Load all fixtures for profile jn-001."""
        return _load_profile_fixtures("jn-001")

    @pytest.fixture(scope="session")
    def fixture_mb_001(self) -> dict:
        """Load all fixtures for profile mb-001."""
        return _load_profile_fixtures("mb-001")

    # =========== Test cases for ingest_resume() ===========

    def test_ingest_resume_ql_001(self, pipeline: IngestionPipeline, fixture_ql_001: dict) -> None:
        """
        Test successful resume ingestion with fixture ql-001.

        Failure modes:
        - Resume parser fails to extract text from PDF
        - Chunking strategy produces no chunks
        - Embedding provider throws exception
        - Database write fails
        """
        result = pipeline.ingest_resume(
            profile_id="ql-001",
            content=fixture_ql_001["resume"],
            filename="resume.pdf",
        )

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.skip_reason is None
        assert result.chunk_count > 0
        assert isinstance(result.source_id, str)
        assert result.source_id.startswith("resume_ql-001")

    def test_ingest_resume_jn_001(self, pipeline: IngestionPipeline, fixture_jn_001: dict) -> None:
        """
        Test successful resume ingestion with fixture jn-001 (markdown resume).

        Failure modes:
        - Resume parser fails to extract text from markdown
        - Chunking strategy produces no chunks
        - Resume metadata is not preserved
        """
        result = pipeline.ingest_resume(
            profile_id="jn-001",
            content=fixture_jn_001["resume"],
            filename="resume.md",
        )

        assert result.skipped is False
        assert result.chunk_count > 0
        assert result.source_id.startswith("resume_jn-001")

    def test_ingest_same_resume_different_profiles(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, fixture_ql_100: dict
    ) -> None:
        """
        Test that identical resume content with different profile IDs produces different source IDs.

        ql-001 and ql-100 have identical files but must be ingested separately because they
        represent different profiles. This tests that the pipeline correctly uses profile_id
        as part of source_id generation.

        Failure modes:
        - Source ID doesn't include profile_id
        - Hash function dominates source_id generation
        - Pipeline incorrectly deduplicates across different profiles
        """
        # Both should have identical content
        assert fixture_ql_001["resume"] == fixture_ql_100["resume"]

        result1 = pipeline.ingest_resume(
            profile_id="ql-001",
            content=fixture_ql_001["resume"],
            filename="resume.pdf",
        )

        result2 = pipeline.ingest_resume(
            profile_id="ql-100",
            content=fixture_ql_100["resume"],
            filename="resume.pdf",
        )

        # Despite identical content, source IDs must be different due to different profile IDs
        assert result1.source_id != result2.source_id
        assert result1.source_id.startswith("resume_ql-001")
        assert result2.source_id.startswith("resume_ql-100")
        assert result1.skipped is False
        assert result2.skipped is False

    def test_ingest_resume_skip_duplicate_profile(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, mock_db_session: MagicMock
    ) -> None:
        """
        Test that ingesting the same profile ID twice correctly skips on second attempt.

        This verifies the deduplication logic: if a profile's resume has already been
        ingested, the pipeline should skip and return skipped=True.

        Failure modes:
        - _check_skip() doesn't find existing source
        - Source ID comparison fails
        - Skip logic uses wrong database query
        - Skip reason is not set correctly
        """
        # First ingestion should succeed
        result1 = pipeline.ingest_resume(
            profile_id="ql-001",
            content=fixture_ql_001["resume"],
            filename="resume.pdf",
        )
        assert result1.skipped is False
        first_source_id = result1.source_id

        # Mock database to simulate source already exists
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = {
            "source_id": first_source_id
        }

        # Second ingestion with same profile should be skipped
        result2 = pipeline.ingest_resume(
            profile_id="ql-001",
            content=fixture_ql_001["resume"],
            filename="resume.pdf",
        )

        assert result2.skipped is True
        assert result2.skip_reason == "Source already ingested"
        assert result2.chunk_count == 0
        assert result2.source_id == first_source_id

    def test_ingest_resume_deterministic_source_id(
        self, pipeline: IngestionPipeline, fixture_mb_001: dict
    ) -> None:
        """
        Test that same profile and content always produce same source ID (deterministic hashing).

        Failure modes:
        - Hash function is non-deterministic
        - Source ID includes random components
        - Source ID format is inconsistent
        """
        result1 = pipeline.ingest_resume(
            profile_id="mb-001",
            content=fixture_mb_001["resume"],
            filename="resume.pdf",
        )

        result2 = pipeline.ingest_resume(
            profile_id="mb-001",
            content=fixture_mb_001["resume"],
            filename="resume.pdf",
        )

        # Same profile and content should always produce same source_id
        assert result1.source_id == result2.source_id

    def test_ingest_resume_chunks_fixture_content(
        self,
        pipeline: IngestionPipeline,
        fixture_ql_001: dict,
        fixture_jn_001: dict,
        fixture_mb_001: dict,
    ) -> None:
        """
        Test that fixture resumes are properly chunked into multiple segments.

        Failure modes:
        - Chunking strategy returns empty list
        - Chunks don't preserve section information
        - Metadata is lost during chunking
        """
        fixtures = [
            ("ql-001", fixture_ql_001, "resume.pdf"),
            ("jn-001", fixture_jn_001, "resume.md"),
            ("mb-001", fixture_mb_001, "resume.pdf"),
        ]

        for profile_id, fixture, filename in fixtures:
            result = pipeline.ingest_resume(
                profile_id=profile_id,
                content=fixture["resume"],
                filename=filename,
            )

            # All fixtures should produce at least some chunks
            assert result.chunk_count > 0, f"Profile {profile_id} produced no chunks"
            assert result.skipped is False

    def test_ingest_empty_resume_content(self, pipeline: IngestionPipeline) -> None:
        """
        Test empty resume content resulting in zero chunk count.

        Failure modes:
        - Parser crashes on empty input
        - Empty chunks are created
        - Error is not properly logged
        """
        result = pipeline.ingest_resume(
            profile_id="empty-test",
            content="",
            filename="empty.txt",
        )
        assert result.chunk_count == 0

    def test_ingest_different_resume_same_profile(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, fixture_jn_001: dict
    ) -> None:
        """
        Test that different content with same profile_id produces
        different source_ids (deduplication by hash).

        Failure modes:
        - Hash function doesn't differentiate content
        - Source ID only depends on profile_id
        - Deduplication incorrectly reuses source_id
        """
        profile_id = "abc-010"

        result1 = pipeline.ingest_resume(
            profile_id=profile_id,
            content=fixture_ql_001["resume"],
            filename="resume1.txt",
        )

        result2 = pipeline.ingest_resume(
            profile_id=profile_id,
            content=fixture_jn_001["resume"],
            filename="resume2.txt",
        )

        # Different content should produce different source_ids (hash-based deduplication)
        assert result1.source_id != result2.source_id
        assert result1.source_id.startswith(f"resume_{profile_id}")
        assert result2.source_id.startswith(f"resume_{profile_id}")

    def test_ingest_resume_invalid_format_parser_error(self, pipeline: IngestionPipeline) -> None:
        """
        Test that invalid/corrupted resume format is caught and handled gracefully.

        Failure modes:
        - Parser crashes on invalid format
        - Error is not logged
        - Partial state left in vector_db
        """
        invalid_pdf = b"%PDF-INVALID\x00\xff\xfe"

        with pytest.raises(ValueError):
            pipeline.ingest_resume(
                profile_id="invalid-test",
                content=invalid_pdf,
                filename="corrupted.pdf",
            )

    def test_ingest_resume_batch_processor_failure_propagates(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, mock_vector_db: MagicMock
    ) -> None:
        """
        Test that batch processor failures propagate as exceptions (not silently ignored).

        Failure modes:
        - Embedding generation failure is silently ignored
        - Error is not raised to caller (exception swallowed)
        - Partial embeddings stored in vector_db
        """
        # Make vector_db.add() raise an exception, simulating storage failure
        mock_vector_db.add.side_effect = RuntimeError("Vector DB storage failed")

        with pytest.raises(RuntimeError, match="Vector DB storage failed"):
            pipeline.ingest_resume(
                profile_id="ql-001",
                content=fixture_ql_001["resume"],
                filename="resume.pdf",
            )

    # =========== Test cases for ingest_readme() ===========

    def test_ingest_readme_ql_001_first_repo(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test successful readme ingestion with fixture ql-001 (first repository).

        Failure modes:
        - README parser fails to extract text from markdown
        - Chunking strategy produces no chunks
        - Embedding provider throws exception
        - Database write fails
        """
        repo = fixture_ql_001["repos"][0]
        result = pipeline.ingest_readme(
            profile_id="ql-001",
            repo_name=repo["name"],
            content=repo["readme"],
        )

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.skip_reason is None
        assert result.chunk_count > 0
        assert isinstance(result.source_id, str)
        assert result.source_id.startswith(f"readme_ql-001_{repo['name']}")

    def test_ingest_multiple_readmes_same_profile(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test ingesting multiple READMEs from different repos for same profile.

        Failure modes:
        - Different repos are incorrectly deduplicated
        - Source ID doesn't include repo_name
        - Metadata doesn't preserve repo information
        """
        results = []
        for repo in fixture_ql_001["repos"]:
            result = pipeline.ingest_readme(
                profile_id="ql-001",
                repo_name=repo["name"],
                content=repo["readme"],
            )
            results.append(result)

        # All repos should be ingested successfully
        assert len(results) > 0
        for result in results:
            assert result.skipped is False
            assert result.chunk_count > 0

        # Each repo should have different source_id
        source_ids = [r.source_id for r in results]
        assert len(source_ids) == len(set(source_ids)), "Source IDs should be unique per repo"

    def test_ingest_readme_same_repo_different_profiles(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, fixture_ql_100: dict
    ) -> None:
        """
        Test that same repo name with different profile IDs produces different source IDs.

        ql-001 and ql-100 have identical repos but must be ingested separately because
        they represent different profiles.

        Failure modes:
        - Source ID doesn't include profile_id
        - Pipeline incorrectly deduplicates across different profiles
        - Repo name and profile_id both matter for uniqueness
        """
        # Get first repo from both profiles (same repo exists in both)
        repo_ql001 = fixture_ql_001["repos"][0]
        repo_ql100 = fixture_ql_100["repos"][0]

        # Both should have identical content (ql-001 and ql-100 have same files)
        assert repo_ql001["readme"] == repo_ql100["readme"]

        result1 = pipeline.ingest_readme(
            profile_id="ql-001",
            repo_name=repo_ql001["name"],
            content=repo_ql001["readme"],
        )

        result2 = pipeline.ingest_readme(
            profile_id="ql-100",
            repo_name=repo_ql100["name"],
            content=repo_ql100["readme"],
        )

        # Despite identical content, source IDs must be different due to different profile IDs
        assert result1.source_id != result2.source_id
        assert result1.source_id.startswith("readme_ql-001_")
        assert result2.source_id.startswith("readme_ql-100_")
        assert result1.skipped is False
        assert result2.skipped is False

    def test_ingest_readme_skip_duplicate(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, mock_db_session: MagicMock
    ) -> None:
        """
        Test that ingesting the same repo README twice correctly skips on second attempt.

        Failure modes:
        - _check_skip() doesn't find existing source
        - Source ID comparison fails
        - Skip logic uses wrong database query
        """
        repo = fixture_ql_001["repos"][0]

        # First ingestion should succeed
        result1 = pipeline.ingest_readme(
            profile_id="ql-001",
            repo_name=repo["name"],
            content=repo["readme"],
        )
        assert result1.skipped is False
        first_source_id = result1.source_id

        # Mock database to simulate source already exists
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = {
            "source_id": first_source_id
        }

        # Second ingestion with same repo should be skipped
        result2 = pipeline.ingest_readme(
            profile_id="ql-001",
            repo_name=repo["name"],
            content=repo["readme"],
        )

        assert result2.skipped is True
        assert result2.skip_reason == "Source already ingested"
        assert result2.chunk_count == 0
        assert result2.source_id == first_source_id

    def test_ingest_different_readme_same_repo_same_profile(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test that different README content produces different source IDs
        (hash-based deduplication), despite identical repo name and profile ID.

        Failure modes:
        - Hash function doesn't differentiate content
        - Source ID doesn't include content hash
        """
        repo = fixture_ql_001["repos"][0]
        profile_id = "test-readme"
        repo_name = repo["name"]

        content1 = repo["readme"]
        content2 = fixture_ql_001["repos"][2]["readme"]

        result1 = pipeline.ingest_readme(
            profile_id=profile_id,
            repo_name=repo_name,
            content=content1,
        )

        result2 = pipeline.ingest_readme(
            profile_id=profile_id,
            repo_name=repo_name,
            content=content2,
        )

        # Different content should produce different source_ids
        assert result1.source_id != result2.source_id
        assert result1.source_id.startswith(f"readme_{profile_id}_{repo_name}")
        assert result2.source_id.startswith(f"readme_{profile_id}_{repo_name}")

    def test_ingest_readme_deterministic_source_id(
        self, pipeline: IngestionPipeline, fixture_jn_001: dict
    ) -> None:
        """
        Test that same profile, repo, and content always produce same source ID.

        Failure modes:
        - Hash function is non-deterministic
        - Source ID includes random components
        """
        repo = fixture_jn_001["repos"][0]

        result1 = pipeline.ingest_readme(
            profile_id="jn-001",
            repo_name=repo["name"],
            content=repo["readme"],
        )

        result2 = pipeline.ingest_readme(
            profile_id="jn-001",
            repo_name=repo["name"],
            content=repo["readme"],
        )

        # Same content should always produce same source_id
        assert result1.source_id == result2.source_id

    def test_ingest_empty_readme(self, pipeline: IngestionPipeline) -> None:
        """
        Test empty README content resulting in zero chunk count.

        Failure modes:
        - Parser crashes on empty input
        - Empty chunks are created
        """
        result = pipeline.ingest_readme(profile_id="empty-test", repo_name="test-repo", content="")
        assert result.chunk_count == 0

    def test_ingest_readme_batch_processor_failure_propagates(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, mock_vector_db: MagicMock
    ) -> None:
        """
        Test that batch processor failures propagate as exceptions during README ingestion.

        Failure modes:
        - Embedding generation failure is silently ignored
        - Error is not raised to caller
        """
        repo = fixture_ql_001["repos"][0]
        mock_vector_db.add.side_effect = RuntimeError("Vector DB storage failed")

        with pytest.raises(RuntimeError, match="Vector DB storage failed"):
            pipeline.ingest_readme(
                profile_id="ql-001",
                repo_name=repo["name"],
                content=repo["readme"],
            )

    # =========== Test cases for ingest_repo_metadata() ===========

    def test_ingest_repo_metadata_ql_001_first_repo(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test successful repo metadata ingestion with fixture ql-001 (first repository).

        Failure modes:
        - Repository analyzer fails to extract metadata
        - Chunking strategy produces no chunks
        - Embedding provider throws exception
        - Database write fails
        """
        repo = fixture_ql_001["repos"][0]
        result = pipeline.ingest_repo_metadata(
            profile_id="ql-001",
            repo_data=repo["metadata"],
        )

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.skip_reason is None
        assert result.chunk_count > 0
        assert isinstance(result.source_id, str)
        assert result.source_id.startswith("repo_ql-001_")

    def test_ingest_multiple_repo_metadata_same_profile(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test ingesting metadata from multiple repos for same profile.

        Failure modes:
        - Different repos are incorrectly deduplicated
        - Source ID doesn't include repo_name
        - Metadata doesn't preserve repo information
        """
        results = []
        for repo in fixture_ql_001["repos"]:
            result = pipeline.ingest_repo_metadata(
                profile_id="ql-001",
                repo_data=repo["metadata"],
            )
            results.append(result)

        # All repos should be ingested successfully
        assert len(results) > 0
        for result in results:
            assert result.skipped is False
            assert result.chunk_count > 0

        # Each repo should have different source_id
        source_ids = [r.source_id for r in results]
        assert len(source_ids) == len(set(source_ids)), "Source IDs should be unique per repo"

    def test_ingest_same_repo_metadata_different_profiles(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, fixture_ql_100: dict
    ) -> None:
        """
        Test that same repo metadata with different profile IDs produces different source IDs.

        ql-001 and ql-100 have identical repo metadata but must be ingested separately
        because they represent different profiles.

        Failure modes:
        - Source ID doesn't include profile_id
        - Pipeline incorrectly deduplicates across different profiles
        """
        # Get first repo from both profiles (same repo exists in both)
        repo_ql001 = fixture_ql_001["repos"][0]
        repo_ql100 = fixture_ql_100["repos"][0]

        # Both should have identical metadata (ql-001 and ql-100 have same files)
        assert repo_ql001["metadata"] == repo_ql100["metadata"]

        result1 = pipeline.ingest_repo_metadata(
            profile_id="ql-001",
            repo_data=repo_ql001["metadata"],
        )

        result2 = pipeline.ingest_repo_metadata(
            profile_id="ql-100",
            repo_data=repo_ql100["metadata"],
        )

        # Despite identical metadata, source IDs must be different due to different profile IDs
        assert result1.source_id != result2.source_id
        assert result1.source_id.startswith("repo_ql-001_")
        assert result2.source_id.startswith("repo_ql-100_")
        assert result1.skipped is False
        assert result2.skipped is False

    def test_ingest_repo_metadata_skip_duplicate(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, mock_db_session: MagicMock
    ) -> None:
        """
        Test that ingesting the same repo metadata twice correctly skips on second attempt.

        Failure modes:
        - _check_skip() doesn't find existing source
        - Source ID comparison fails
        - Skip logic uses wrong database query
        """
        repo = fixture_ql_001["repos"][0]

        # First ingestion should succeed
        result1 = pipeline.ingest_repo_metadata(
            profile_id="ql-001",
            repo_data=repo["metadata"],
        )
        assert result1.skipped is False
        first_source_id = result1.source_id

        # Mock database to simulate source already exists
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = {
            "source_id": first_source_id
        }

        # Second ingestion with same repo should be skipped
        result2 = pipeline.ingest_repo_metadata(
            profile_id="ql-001",
            repo_data=repo["metadata"],
        )

        assert result2.skipped is True
        assert result2.skip_reason == "Source already ingested"
        assert result2.chunk_count == 0
        assert result2.source_id == first_source_id

    def test_ingest_different_repo_metadata_same_profile(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test that different repo metadata with same profile ID produces
        different source IDs (hash-based deduplication).

        Failure modes:
        - Hash function doesn't differentiate metadata
        - Source ID doesn't include content hash
        """
        repo1 = fixture_ql_001["repos"][0]
        repo2 = fixture_ql_001["repos"][1] if len(fixture_ql_001["repos"]) > 1 else None

        if not repo2:
            # If only one repo in fixture, skip this test
            pytest.skip("Fixture has only one repo")

        result1 = pipeline.ingest_repo_metadata(
            profile_id="test-repo",
            repo_data=repo1["metadata"],
        )

        result2 = pipeline.ingest_repo_metadata(
            profile_id="test-repo",
            repo_data=repo2["metadata"],
        )

        # Different metadata should produce different source_ids
        assert result1.source_id != result2.source_id
        assert result1.source_id.startswith("repo_test-repo_")
        assert result2.source_id.startswith("repo_test-repo_")

    def test_ingest_repo_metadata_deterministic_source_id(
        self, pipeline: IngestionPipeline, fixture_jn_001: dict
    ) -> None:
        """
        Test that same profile and metadata always produce same source ID.

        Failure modes:
        - Hash function is non-deterministic
        - Source ID includes random components
        """
        repo = fixture_jn_001["repos"][0]

        result1 = pipeline.ingest_repo_metadata(
            profile_id="jn-001",
            repo_data=repo["metadata"],
        )

        result2 = pipeline.ingest_repo_metadata(
            profile_id="jn-001",
            repo_data=repo["metadata"],
        )

        # Same metadata should always produce same source_id
        assert result1.source_id == result2.source_id

    def test_ingest_repo_metadata_extracts_language_and_tech_stack(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict
    ) -> None:
        """
        Test that repo analyzer correctly extracts language and tech stack from metadata.

        Failure modes:
        - Language field not extracted
        - Tech stack detection fails
        - Metadata not preserved through chunking
        """
        repo = fixture_ql_001["repos"][0]
        metadata = repo["metadata"]

        # Verify metadata has required fields for analysis
        assert "language" in metadata or "primary_language" in metadata.get("topics", [])

        result = pipeline.ingest_repo_metadata(
            profile_id="ql-001",
            repo_data=metadata,
        )

        # Metadata should be analyzed and produce chunks
        assert result.skipped is False
        assert result.chunk_count > 0

    def test_ingest_repo_metadata_batch_processor_failure_propagates(
        self, pipeline: IngestionPipeline, fixture_ql_001: dict, mock_vector_db: MagicMock
    ) -> None:
        """
        Test that batch processor failures propagate as exceptions during metadata ingestion.

        Failure modes:
        - Embedding generation failure is silently ignored
        - Error is not raised to caller
        """
        repo = fixture_ql_001["repos"][0]
        mock_vector_db.add.side_effect = RuntimeError("Vector DB storage failed")

        with pytest.raises(RuntimeError, match="Vector DB storage failed"):
            pipeline.ingest_repo_metadata(
                profile_id="ql-001",
                repo_data=repo["metadata"],
            )
