"""Tests that structlog output is captured by pytest's ``caplog`` fixture.

Regression tests for issue #159: structlog was rendering events straight to
stdout instead of routing them through standard-library logging, so ``caplog``
captured nothing and every log-based assertion failed suite-wide. The autouse
``structlog_to_stdlib_logging`` fixture in ``tests/conftest.py`` fixes this; the
tests below lock in the behavior across log levels, bound structured fields, and
loggers bound at import time.
"""

import logging

import pytest
import structlog


@pytest.mark.unit
class TestStructlogCaplogCapture:
    """Verify structlog records reach ``caplog`` for the fix in issue #159."""

    def test_warning_is_captured_in_text(self, caplog):
        """A warning-level structlog event appears in ``caplog.text``."""
        logger = structlog.get_logger("test.warning")

        logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")

        assert "Empty chunks list provided to BatchEmbeddingProcessor" in caplog.text

    def test_warning_produces_a_log_record(self, caplog):
        """The event becomes a real ``LogRecord`` with the expected level."""
        logger = structlog.get_logger("test.record")

        logger.warning("something happened")

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelno == logging.WARNING
        assert "something happened" in record.getMessage()

    def test_info_level_captured_when_level_lowered(self, caplog):
        """Info events are captured once the effective level allows them.

        By default the root logger sits at WARNING, so info records are filtered
        by stdlib logging before they reach the capture handler. Lowering the
        level with ``caplog.set_level`` — the idiomatic pytest approach — lets
        the info event through.
        """
        caplog.set_level(logging.INFO)
        logger = structlog.get_logger("test.info")

        logger.info("Starting batch embedding processing")

        assert "Starting batch embedding processing" in caplog.text

    def test_error_level_captured(self, caplog):
        """Error-level structlog events are captured."""
        logger = structlog.get_logger("test.error")

        logger.error("Failed to store embedding")

        assert any(r.levelno == logging.ERROR for r in caplog.records)
        assert "Failed to store embedding" in caplog.text

    def test_bound_structured_fields_do_not_break_capture(self, caplog):
        """Extra key/values are attached to the record without breaking capture.

        ``render_to_log_kwargs`` forwards bound fields as ``extra`` on the
        ``LogRecord``, so the message stays assertable and the structured data is
        still available on the captured record.
        """
        caplog.set_level(logging.INFO)
        logger = structlog.get_logger("test.bound")

        logger.info("Starting batch embedding processing", chunk_count=42)

        assert "Starting batch embedding processing" in caplog.text
        record = caplog.records[0]
        assert record.chunk_count == 42

    def test_import_time_bound_logger_is_captured(self, caplog):
        """A logger bound at import time still routes through stdlib logging.

        ``BatchEmbeddingProcessor`` binds ``logger = structlog.get_logger()`` at
        import, before this fixture runs. With ``cache_logger_on_first_use=False``
        the lazy proxy re-reads the test configuration on its next call, so its
        warning is captured — the original failing scenario from issue #159.
        """
        from ingestion.embeddings.batch_processor import BatchEmbeddingProcessor

        processor = BatchEmbeddingProcessor(embedding_provider=object(), vector_db=object())

        result = processor.process([])

        assert result == []
        assert "Empty chunks list" in caplog.text
