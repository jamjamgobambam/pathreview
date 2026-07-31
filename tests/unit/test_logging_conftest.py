"""Tests for the structlog/caplog bridge fixture in tests/conftest.py (issue #159)."""

import logging

import pytest
import structlog


@pytest.mark.unit
class TestStructlogCaplogBridge:
    """Verify structlog output reaches pytest's caplog, suite-wide."""

    def test_structlog_event_appears_in_caplog_text(self, caplog: pytest.LogCaptureFixture) -> None:
        """A plain structlog.get_logger() call should be visible in caplog.text."""
        logger = structlog.get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("some_structlog_event", detail="value")

        assert "some_structlog_event" in caplog.text

    def test_structlog_warning_appears_in_caplog_records(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """caplog.records should carry the correct stdlib log level."""
        logger = structlog.get_logger(__name__)

        with caplog.at_level(logging.WARNING):
            logger.warning("another_event")

        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_bound_context_does_not_break_message_capture(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Bound key/value context shouldn't prevent the event text from being captured."""
        logger = structlog.get_logger(__name__).bind(request_id="abc123")

        with caplog.at_level(logging.INFO):
            logger.info("bound_context_event")

        assert "bound_context_event" in caplog.text
