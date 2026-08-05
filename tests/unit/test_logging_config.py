"""Tests for structlog/caplog integration (issue #159)."""

import pytest
import structlog


def test_configure_logging_enables_caplog_capture(caplog: pytest.LogCaptureFixture) -> None:
    """Regression test for #159: structlog events should be captured by caplog.

    Prior to the fix, configure_logging() was never called during tests,
    so structlog fell back to its default PrintLoggerFactory and log
    events never reached caplog's stdlib logging handler.
    """
    log = structlog.get_logger()

    with caplog.at_level("WARNING"):
        log.warning("test message for caplog capture")

    assert "test message for caplog capture" in caplog.text
