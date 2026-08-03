"""Tests for core/logging.py configuration."""

import pytest
import structlog


@pytest.mark.unit
def test_structlog_output_captured_by_caplog(caplog: pytest.LogCaptureFixture) -> None:
    """Test that structlog messages propagate to stdlib logging so caplog can see them."""
    logger = structlog.get_logger()
    logger.warning("test_log_message", detail="some_value")

    assert "test_log_message" in caplog.text
