"""Regression tests for structlog -> stdlib logging propagation (issue #159).

The app configures structlog only at startup (``core.logging.configure_logging``),
which is never called during tests. Without the autouse ``configure_structlog_for_caplog``
fixture in ``tests/conftest.py``, structlog falls back to its default ``PrintLogger`` and
writes straight to stdout/stderr, so pytest's ``caplog`` fixture captures nothing and any
``caplog``-based assertion fails suite-wide.

These tests pin that fixture's behavior: structlog events must reach the stdlib ``logging``
system so ``caplog`` can observe them.
"""

import logging

import pytest
import structlog


@pytest.mark.unit
class TestStructlogCaplogPropagation:
    """Ensure structlog events propagate into pytest's caplog."""

    def test_warning_is_captured_without_level_setup(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A warning event should land in caplog with no extra configuration."""
        log = structlog.get_logger("regression.test")

        log.warning("regression warning event")

        assert "regression warning event" in caplog.text

    def test_info_is_captured_with_level_set(self, caplog: pytest.LogCaptureFixture) -> None:
        """Info-level events are captured once the level is lowered via caplog."""
        log = structlog.get_logger("regression.test")

        with caplog.at_level(logging.INFO):
            log.info("regression info event")

        assert "regression info event" in caplog.text

    def test_key_value_context_reaches_log_record(self, caplog: pytest.LogCaptureFixture) -> None:
        """structlog key/value context should be reachable as LogRecord attributes."""
        log = structlog.get_logger("regression.test")

        with caplog.at_level(logging.INFO):
            log.info("event with context", chunk_count=7)

        assert any(getattr(record, "chunk_count", None) == 7 for record in caplog.records)
