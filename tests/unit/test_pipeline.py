"""Tests for pipeline.py — ingestion idempotency (issue #6).

The pipeline is exercised against a fake AsyncSession that mimics the parts of
SQLAlchemy's contract it actually uses (execute/add/commit/rollback, plus the
unique constraint on source_id). That keeps these unit tests dependency-free
while still testing _check_skip and _record_ingested_source together, which is
where the bug lived — each half was individually broken.
"""

from typing import Any
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from ingestion.pipeline import IngestionPipeline

PROFILE_A = "11111111-1111-1111-1111-111111111111"
PROFILE_B = "22222222-2222-2222-2222-222222222222"

README = """# TaskTracker

A todo app built with FastAPI and React.

## Features

- Create, edit, and complete tasks
- Tag-based filtering and search

## Setup

Run `make dev` and open localhost:3000.
"""

RESUME = """
Jane Doe
Software Engineer

Experience:
- Software Engineer at TechCorp (2022-2024)

Skills: Python, FastAPI, PostgreSQL
"""


def repo_payload(**overrides: Any) -> dict:
    """A GitHub-shaped repo payload; override any field per test."""
    data = {
        "name": "tasktracker",
        "description": "A todo app built with FastAPI and React",
        "language": "Python",
        "languages": {"Python": 6000, "TypeScript": 4000},
        "topics": ["fastapi", "react"],
        "html_url": "https://github.com/example/tasktracker",
        "stargazers_count": 41,
        "forks_count": 3,
        "open_issues_count": 2,
        "pushed_at": "2026-07-14T10:00:00Z",
    }
    data.update(overrides)
    return data


class UniqueViolationError(Exception):
    """Stand-in for asyncpg.exceptions.UniqueViolationError."""

    sqlstate = "23505"


class ForeignKeyViolationError(Exception):
    """Stand-in for asyncpg.exceptions.ForeignKeyViolationError."""

    sqlstate = "23503"


def db_down() -> OperationalError:
    """The database being unreachable, as SQLAlchemy surfaces it."""
    return OperationalError("SELECT 1", {}, ConnectionError("connection reset"))


class FakeResult:
    def __init__(self, row: Any) -> None:
        self._row = row

    def scalar_one_or_none(self) -> Any:
        return self._row


class FakeAsyncSession:
    """Minimal AsyncSession stand-in with a real uniqueness check on source_id."""

    def __init__(self) -> None:
        self.rows: dict[str, Any] = {}
        self.pending: list[Any] = []
        self.commits = 0
        self.rollbacks = 0
        self.execute_error: Exception | None = None
        self.commit_error: Exception | None = None

    async def execute(self, statement: Any) -> FakeResult:
        if self.execute_error is not None:
            raise self.execute_error
        params = statement.compile().params
        source_id = next(iter(params.values()))
        return FakeResult(self.rows.get(source_id))

    def add(self, obj: Any) -> None:
        self.pending.append(obj)

    async def commit(self) -> None:
        if self.commit_error is not None:
            self.pending.clear()
            raise self.commit_error
        for obj in self.pending:
            if obj.source_id in self.rows:
                self.pending.clear()
                raise IntegrityError("INSERT", {}, UniqueViolationError())
            self.rows[obj.source_id] = obj
        self.pending.clear()
        self.commits += 1

    async def rollback(self) -> None:
        self.pending.clear()
        self.rollbacks += 1


@pytest.mark.unit
class TestIngestionIdempotency:
    """Re-ingesting unchanged content must be a recorded no-op (issue #6)."""

    @pytest.fixture
    def session(self) -> FakeAsyncSession:
        return FakeAsyncSession()

    @pytest.fixture
    def provider(self) -> Mock:
        provider = Mock()
        provider.embed = Mock(side_effect=lambda texts: [[0.1] * 1536 for _ in texts])
        return provider

    @pytest.fixture
    def vector_db(self) -> Mock:
        return Mock()

    @pytest.fixture
    def pipeline(
        self, vector_db: Mock, session: FakeAsyncSession, provider: Mock
    ) -> IngestionPipeline:
        return IngestionPipeline(
            vector_db=vector_db, db_session=session, embedding_provider=provider
        )

    # ---- core idempotency ------------------------------------------------

    @pytest.mark.asyncio
    async def test_second_identical_readme_ingest_is_skipped(
        self, pipeline: IngestionPipeline
    ) -> None:
        first = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)
        second = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert first.skipped is False
        assert second.skipped is True
        assert second.chunk_count == 0
        assert second.skip_reason == "Source already ingested"
        assert second.source_id == first.source_id

    @pytest.mark.asyncio
    async def test_skipped_ingest_does_not_re_bill_embedding_provider(
        self, pipeline: IngestionPipeline, provider: Mock
    ) -> None:
        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)
        calls_after_first = provider.embed.call_count

        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert calls_after_first > 0, "first ingest should embed"
        assert provider.embed.call_count == calls_after_first

    @pytest.mark.asyncio
    async def test_skipped_ingest_does_not_write_to_vector_store(
        self, pipeline: IngestionPipeline, vector_db: Mock
    ) -> None:
        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)
        adds_after_first = vector_db.add.call_count

        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert adds_after_first > 0, "first ingest should write vectors"
        assert vector_db.add.call_count == adds_after_first

    @pytest.mark.asyncio
    async def test_first_ingest_records_exactly_one_row(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession
    ) -> None:
        result = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)
        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert list(session.rows) == [result.source_id]
        row = session.rows[result.source_id]
        assert row.profile_id == PROFILE_A
        assert row.source_type == "readme"
        assert row.chunk_count == result.chunk_count
        assert len(row.content_hash) == 64, "content_hash should be a full SHA-256"

    # ---- repo hash stability --------------------------------------------

    @pytest.mark.asyncio
    async def test_repo_hash_ignores_volatile_fields(self, pipeline: IngestionPipeline) -> None:
        first = await pipeline.ingest_repo_metadata(PROFILE_A, repo_payload())
        second = await pipeline.ingest_repo_metadata(
            PROFILE_A,
            repo_payload(
                stargazers_count=42,
                forks_count=9,
                open_issues_count=7,
                pushed_at="2026-07-21T09:00:00Z",
            ),
        )

        assert second.source_id == first.source_id
        assert second.skipped is True

    @pytest.mark.asyncio
    async def test_repo_hash_ignores_key_ordering(self, pipeline: IngestionPipeline) -> None:
        forward = repo_payload()
        reordered = dict(reversed(list(forward.items())))

        first = await pipeline.ingest_repo_metadata(PROFILE_A, forward)
        second = await pipeline.ingest_repo_metadata(PROFILE_A, reordered)

        assert second.source_id == first.source_id
        assert second.skipped is True

    @pytest.mark.asyncio
    async def test_repo_hash_reacts_to_description_change(
        self, pipeline: IngestionPipeline
    ) -> None:
        first = await pipeline.ingest_repo_metadata(PROFILE_A, repo_payload())
        second = await pipeline.ingest_repo_metadata(
            PROFILE_A, repo_payload(description="Now a Kubernetes operator")
        )

        assert second.source_id != first.source_id
        assert second.skipped is False

    @pytest.mark.asyncio
    async def test_repo_hash_reacts_to_topics_change(self, pipeline: IngestionPipeline) -> None:
        first = await pipeline.ingest_repo_metadata(PROFILE_A, repo_payload())
        second = await pipeline.ingest_repo_metadata(
            PROFILE_A, repo_payload(topics=["fastapi", "react", "kubernetes"])
        )

        assert second.source_id != first.source_id
        assert second.skipped is False

    # ---- scoping edge cases ---------------------------------------------

    @pytest.mark.asyncio
    async def test_identical_content_across_profiles_is_not_deduplicated(
        self, pipeline: IngestionPipeline
    ) -> None:
        first = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)
        second = await pipeline.ingest_readme(PROFILE_B, "tasktracker", README)

        assert second.source_id != first.source_id
        assert second.skipped is False

    @pytest.mark.asyncio
    async def test_same_resume_under_a_different_filename_is_skipped(
        self, pipeline: IngestionPipeline
    ) -> None:
        first = await pipeline.ingest_resume(PROFILE_A, RESUME, "resume.md")
        second = await pipeline.ingest_resume(PROFILE_A, RESUME, "resume-final-v2.md")

        assert second.source_id == first.source_id
        assert second.skipped is True

    @pytest.mark.asyncio
    async def test_recorded_row_keeps_the_first_filename(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession
    ) -> None:
        first = await pipeline.ingest_resume(PROFILE_A, RESUME, "resume.md")
        await pipeline.ingest_resume(PROFILE_A, RESUME, "resume-final-v2.md")

        assert session.rows[first.source_id].filename == "resume.md"

    # ---- failure paths ---------------------------------------------------

    @pytest.mark.asyncio
    async def test_skip_check_db_error_proceeds_with_ingestion(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession, provider: Mock
    ) -> None:
        session.execute_error = db_down()

        result = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert result.skipped is False
        assert result.chunk_count > 0
        assert provider.embed.call_count > 0

    @pytest.mark.asyncio
    async def test_concurrent_record_race_does_not_fail_the_ingest(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession
    ) -> None:
        # Another worker slipped a row in between our _check_skip and our commit.
        session.commit_error = IntegrityError("INSERT", {}, UniqueViolationError())

        result = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert result.skipped is False
        assert session.rollbacks == 1

    @pytest.mark.asyncio
    async def test_foreign_key_violation_is_not_treated_as_a_dedup_race(
        self,
        pipeline: IngestionPipeline,
        session: FakeAsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # An unknown profile_id is a real bug and must not be logged as a benign
        # "already recorded by a concurrent ingest". structlog bypasses caplog, so
        # assert against the module logger directly.
        spy = Mock()
        monkeypatch.setattr("ingestion.pipeline.logger", spy)
        session.commit_error = IntegrityError("INSERT", {}, ForeignKeyViolationError())

        result = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert result.skipped is False
        assert session.rollbacks == 1
        assert any(
            call.args and "Failed to record" in call.args[0] for call in spy.error.call_args_list
        ), f"expected an error log, got {spy.error.call_args_list}"
        assert not any(
            call.args and "concurrent" in call.args[0].lower() for call in spy.info.call_args_list
        )

    @pytest.mark.asyncio
    async def test_unique_violation_is_logged_as_a_dedup_race(
        self,
        pipeline: IngestionPipeline,
        session: FakeAsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        spy = Mock()
        monkeypatch.setattr("ingestion.pipeline.logger", spy)
        session.commit_error = IntegrityError("INSERT", {}, UniqueViolationError())

        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert any(
            call.args and "concurrent" in call.args[0].lower() for call in spy.info.call_args_list
        ), f"expected a concurrent-ingest log, got {spy.info.call_args_list}"
        assert spy.error.call_args_list == []

    @pytest.mark.asyncio
    async def test_skip_check_db_error_is_logged_at_error_level(
        self,
        pipeline: IngestionPipeline,
        session: FakeAsyncSession,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # The original bug hid behind a warning nobody reads.
        spy = Mock()
        monkeypatch.setattr("ingestion.pipeline.logger", spy)
        session.execute_error = db_down()

        await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert any(
            call.args and "Could not check" in call.args[0] for call in spy.error.call_args_list
        ), f"expected an error log, got {spy.error.call_args_list}"
        assert spy.warning.call_args_list == []

    @pytest.mark.asyncio
    async def test_attribute_error_in_skip_check_is_not_swallowed(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession
    ) -> None:
        # Regression guard for the root cause of issue #6: the broken query was an
        # AttributeError hidden by a bare `except Exception`, which silently turned
        # deduplication off. Only database errors are tolerated; anything else must
        # surface rather than degrade the pipeline to its old no-op behavior.
        session.execute_error = AttributeError("'AsyncSession' object has no attribute 'query'")

        with pytest.raises(AttributeError):
            await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

    @pytest.mark.asyncio
    async def test_failed_recording_leaves_the_source_unskipped(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession
    ) -> None:
        # If recording fails, the next ingest must retry rather than skip on a
        # row that was never persisted.
        session.commit_error = db_down()
        first = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        session.commit_error = None
        second = await pipeline.ingest_readme(PROFILE_A, "tasktracker", README)

        assert first.skipped is False
        assert second.skipped is False
        assert list(session.rows) == [second.source_id]

    @pytest.mark.asyncio
    async def test_empty_content_is_still_recorded_so_re_upload_skips(
        self, pipeline: IngestionPipeline, session: FakeAsyncSession
    ) -> None:
        first = await pipeline.ingest_resume(PROFILE_A, "   ", "empty.md")
        second = await pipeline.ingest_resume(PROFILE_A, "   ", "empty.md")

        assert first.skipped is False
        assert second.skipped is True
        assert session.rows[first.source_id].chunk_count == first.chunk_count
