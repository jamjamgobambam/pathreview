"""Tests for the shared test logging configuration."""

import logging

import pytest
import structlog


@pytest.mark.unit
def test_structlog_warning_is_captured_by_caplog(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that structlog events become standard logging records."""
    logger = structlog.get_logger("test.logging")

    with caplog.at_level(logging.WARNING):
        logger.warning("structured warning", issue=159)

    record = next(
        record for record in caplog.records if record.getMessage() == "structured warning"
    )
    assert record.levelno == logging.WARNING
    assert record.issue == 159
