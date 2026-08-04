"""Regression tests for structlog events reaching pytest's caplog (issue #159).

The logger below is bound at module import time on purpose: application modules such
as ``ingestion/embeddings/batch_processor.py`` bind theirs the same way, and that is
the path that used to bypass stdlib logging entirely -- structlog's default
``PrintLoggerFactory`` wrote to stdout, so ``caplog`` stayed empty. The autouse
``configure_structlog_for_tests`` fixture in ``tests/conftest.py`` is what makes these
assertions hold.
"""

import logging

import pytest
import structlog

logger = structlog.get_logger()


@pytest.mark.unit
class TestStructlogCaplogCapture:
    """structlog output must be visible to ``caplog``, not just to stdout."""

    def test_warning_is_captured_with_level_and_message(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A warning emitted through structlog reaches caplog verbatim."""
        message = "Empty chunks list provided to BatchEmbeddingProcessor"

        logger.warning(message)

        records = [record for record in caplog.records if record.message == message]
        assert len(records) == 1
        assert records[0].levelname == "WARNING"
        assert message in caplog.text

    def test_bound_values_do_not_leak_into_the_message(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured key/values ride along as record attributes, not in the message."""
        with caplog.at_level(logging.INFO):
            logger.info("Batch embedded", batch_size=100)

        records = [record for record in caplog.records if record.message == "Batch embedded"]
        assert len(records) == 1
        assert records[0].levelname == "INFO"
        assert records[0].batch_size == 100
