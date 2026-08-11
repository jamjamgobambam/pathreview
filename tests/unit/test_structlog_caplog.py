"""Unit tests for structlog → pytest caplog integration (issue #159)."""

import pytest
import structlog


@pytest.mark.unit
class TestStructlogCaplogCapture:
    """Verify structlog events are visible to pytest's caplog fixture."""

    def test_warning_appears_in_caplog_text(self, caplog: pytest.LogCaptureFixture) -> None:
        """structlog warning event text is searchable via caplog.text."""
        logger = structlog.get_logger("tests.structlog_caplog")
        logger.warning("caplog capture probe")

        assert "caplog capture probe" in caplog.text

    def test_warning_appears_in_caplog_records(self, caplog: pytest.LogCaptureFixture) -> None:
        """structlog warning is present as a stdlib LogRecord in caplog.records."""
        logger = structlog.get_logger("tests.structlog_caplog")
        logger.warning("caplog capture probe")

        assert any("caplog capture probe" in record.getMessage() for record in caplog.records)
        assert any(record.levelname == "WARNING" for record in caplog.records)
