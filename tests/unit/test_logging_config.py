"""Regression tests for shared pytest structlog configuration."""

import logging

import pytest
import structlog

_PROBE_EVENT = "shared_conftest_routing_probe"
_PROBE_FIELD_VALUE = "caplog-visible"
_logger = structlog.get_logger("tests.logging_config_probe")


@pytest.mark.unit
def test_shared_conftest_routes_structlog_to_caplog(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Route an import-time structlog logger through stdlib exactly once."""
    with caplog.at_level(logging.INFO):
        _logger.info(_PROBE_EVENT, routing_probe=_PROBE_FIELD_VALUE)

    matching_records = [record for record in caplog.records if _PROBE_EVENT in record.getMessage()]

    assert len(matching_records) == 1
    record = matching_records[0]
    assert record.levelno == logging.INFO
    assert _PROBE_EVENT in record.getMessage()
    assert "routing_probe" in record.getMessage()
    assert _PROBE_FIELD_VALUE in record.getMessage()
