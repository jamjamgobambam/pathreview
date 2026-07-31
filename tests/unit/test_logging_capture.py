"""Tests for structlog events reaching pytest's caplog fixture.

These tests exercise the autouse fixture in ``tests/conftest.py`` that bridges
structlog into the standard library ``logging`` module. Without that bridge,
structlog uses its default ``PrintLoggerFactory``, which writes rendered events
straight to stdout and never creates a ``LogRecord`` — so ``caplog``, which is
implemented as a stdlib logging handler, captures nothing.

The probe logger here is deliberately independent of application code: the unit
under test is the test-environment configuration, not any particular module that
happens to log.
"""

import logging

import pytest
import structlog

LOGGER_NAME = "tests.logging_probe"


@pytest.mark.unit
class TestStructlogCaplogCapture:
    """Test suite for structlog-to-caplog capture in the test environment."""

    def test_warning_creates_a_captured_log_record(self, caplog: pytest.LogCaptureFixture) -> None:
        """A structlog warning becomes a stdlib LogRecord that caplog captures."""
        structlog.get_logger(LOGGER_NAME).warning("probe warning event")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"

    def test_record_name_matches_the_emitting_logger(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The captured record carries the name passed to get_logger()."""
        structlog.get_logger(LOGGER_NAME).warning("named probe event")

        assert caplog.records[0].name == LOGGER_NAME

    def test_bound_context_renders_into_captured_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured key/value pairs survive into the captured message text."""
        structlog.get_logger(LOGGER_NAME).warning("probe with context", chunk_count=3)

        assert "chunk_count" in caplog.text
        assert "3" in caplog.text

    def test_info_is_dropped_until_the_test_lowers_the_level(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """INFO events need an explicit level opt-in; the fixture must not force it."""
        structlog.get_logger(LOGGER_NAME).info("info below the default level")

        assert caplog.records == []

        with caplog.at_level(logging.INFO):
            structlog.get_logger(LOGGER_NAME).info("info above the lowered level")

        assert [record.levelname for record in caplog.records] == ["INFO"]

    def test_a_silent_test_captures_nothing(self, caplog: pytest.LogCaptureFixture) -> None:
        """The fixture itself must not emit configuration or startup noise."""
        assert caplog.records == []
