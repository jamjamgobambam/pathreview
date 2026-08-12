"""Tests that structlog events are visible to pytest's caplog fixture."""

import logging

import pytest
import structlog


@pytest.mark.unit
def test_structlog_warning_is_captured_by_caplog(caplog: pytest.LogCaptureFixture) -> None:
    """structlog warnings should appear in caplog via the test conftest wiring."""
    logger = structlog.get_logger("tests.structlog_caplog")

    with caplog.at_level(logging.WARNING):
        logger.warning("Empty chunks list provided to BatchEmbeddingProcessor")

    assert "Empty chunks list" in caplog.text
    assert any("Empty chunks list" in record.getMessage() for record in caplog.records)


@pytest.mark.unit
def test_structlog_info_is_captured_when_level_allows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Info-level structlog events are capturable when caplog level permits."""
    logger = structlog.get_logger("tests.structlog_caplog")

    with caplog.at_level(logging.INFO):
        logger.info("Starting batch embedding processing", chunk_count=0)

    assert "Starting batch embedding processing" in caplog.text
