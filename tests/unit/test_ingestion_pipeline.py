"""Tests for README ingestion + skip check (issue #13: conditional hash re-embedding).

These exercise the skip functionality THROUGH `IngestionPipeline.ingest_readme` (rather
than calling `_check_skip` directly), so they describe the real round-trip contract:

    ingest a README  ->  it is embedded and recorded
    ingest the SAME README again  ->  it is skipped, NOT re-embedded
    ingest a CHANGED README  ->  it is embedded again

The DB is a small in-memory fake that stores whatever the pipeline `.add()`s and returns
it on lookup, so the tests assert observable behavior rather than a specific ORM/field.
"""

from unittest.mock import Mock

import pytest

from ingestion.pipeline import IngestionPipeline


class _FakeQuery:
    """Minimal stand-in for a SQLAlchemy query supporting filter_by(...).first()."""

    def __init__(self, records):
        self._records = records
        self._filters = {}

    def filter_by(self, **kwargs):
        self._filters = kwargs
        return self

    def first(self):
        for record in self._records:
            if all(getattr(record, k, None) == v for k, v in self._filters.items()):
                return record
        return None


class _FakeSession:
    """Stateful in-memory session: records added rows and serves them back on query."""

    def __init__(self):
        self.records = []

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self.records)

    def add(self, obj):
        self.records.append(obj)

    def commit(self):
        pass


@pytest.mark.unit
class TestReadmeIngestSkip:
    """Skip behavior verified end-to-end through ingest_readme."""

    CONTENT = "# My Project\n\n## Setup\n```bash\npip install .\n```\n"

    @pytest.fixture
    def db(self):
        return _FakeSession()

    @pytest.fixture
    def pipeline(self, db):
        """Pipeline with real parser but mocked chunking/embedding for isolation."""
        p = IngestionPipeline(
            vector_db=Mock(),
            db_session=db,
            embedding_provider=Mock(),
        )
        # Chunking yields two fake chunks; embedding is a no-op we can count.
        p.strategy_selector = Mock()
        p.strategy_selector.chunk = Mock(return_value=[Mock(), Mock()])
        p.batch_processor = Mock()
        p.batch_processor.process = Mock(return_value=[])
        return p

    def test_first_ingest_embeds_and_is_not_skipped(self, pipeline):
        """A README seen for the first time is parsed, chunked, and embedded."""
        result = pipeline.ingest_readme("p1", "my-repo", self.CONTENT)

        assert result.skipped is False
        assert result.chunk_count == 2
        pipeline.batch_processor.process.assert_called_once()

    def test_re_ingesting_identical_readme_is_skipped(self, pipeline):
        """Ingesting the same README a second time must be skipped (issue #13)."""
        pipeline.ingest_readme("p1", "my-repo", self.CONTENT)

        second = pipeline.ingest_readme("p1", "my-repo", self.CONTENT)

        assert second.skipped is True
        assert second.chunk_count == 0

    def test_re_ingesting_identical_readme_does_not_re_embed(self, pipeline):
        """The whole point: unchanged content must not be embedded twice."""
        pipeline.ingest_readme("p1", "my-repo", self.CONTENT)
        pipeline.ingest_readme("p1", "my-repo", self.CONTENT)

        # Exactly one embedding pass across the two identical ingestions.
        assert pipeline.batch_processor.process.call_count == 1

    def test_identical_content_as_bytes_is_also_skipped(self, pipeline):
        """str and its utf-8 bytes are the same content and must not double-embed."""
        pipeline.ingest_readme("p1", "my-repo", self.CONTENT)

        second = pipeline.ingest_readme("p1", "my-repo", self.CONTENT.encode("utf-8"))

        assert second.skipped is True
        assert pipeline.batch_processor.process.call_count == 1

    def test_changed_readme_is_re_embedded(self, pipeline):
        """Different content must NOT be skipped — it is embedded again."""
        pipeline.ingest_readme("p1", "my-repo", "# V1\nfirst version")

        second = pipeline.ingest_readme("p1", "my-repo", "# V2\nsecond, changed version")

        assert second.skipped is False
        assert second.chunk_count == 2
        assert pipeline.batch_processor.process.call_count == 2

    def test_different_repo_with_same_content_is_not_skipped(self, pipeline):
        """Same content in a different repo is a different source and must be embedded."""
        pipeline.ingest_readme("p1", "repo1", self.CONTENT)

        second = pipeline.ingest_readme("p1", "repo2", self.CONTENT)

        assert second.skipped is False
        assert second.chunk_count == 2
        assert pipeline.batch_processor.process.call_count == 2
