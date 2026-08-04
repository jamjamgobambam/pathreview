"""Regression tests for structlog <-> pytest caplog integration (issue #159).

structlog's default ``PrintLogger`` writes to stdout and bypasses stdlib
logging, so ``caplog`` captured nothing and log assertions failed suite-wide.
The autouse ``route_structlog_to_stdlib`` fixture in ``tests/conftest.py`` routes
structlog through the stdlib ``LoggerFactory``; these tests lock that behaviour in.
"""

import logging

import pytest
import structlog


@pytest.mark.unit
class TestStructlogCaplogCapture:
    """structlog records emitted in tests must be visible to caplog."""

    def test_warning_is_captured_in_caplog(self, caplog):
        """A structlog warning reaches both caplog.text and caplog.records."""
        log = structlog.get_logger("test.caplog.warning")

        log.warning("Empty chunks list provided to X", chunk_count=0)

        assert "Empty chunks list" in caplog.text
        assert any("empty chunks list" in r.message.lower() for r in caplog.records)

    def test_info_is_captured_when_level_lowered(self, caplog):
        """caplog.set_level(INFO) lets structlog info records through too."""
        log = structlog.get_logger("test.caplog.info")

        with caplog.at_level(logging.INFO):
            log.info("batch embedding complete", stored_count=3)

        assert "batch embedding complete" in caplog.text

    def test_structured_key_values_are_rendered(self, caplog):
        """Bound key/value context is rendered into the captured record."""
        log = structlog.get_logger("test.caplog.kv")

        log.warning("pii detected", count=2)

        assert "count=2" in caplog.text
