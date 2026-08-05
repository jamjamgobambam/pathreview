import pytest

@pytest.mark.unit
def test_caplog_sees_bare_structlog_output(caplog):
    import structlog

    logger = structlog.get_logger()
    logger.warning("testing to see if log recieved")
    assert "testing to see if log recieved" in caplog.text

@pytest.mark.unit
def test_caplog_sees_custom_core_logging_output(caplog):
    from core.logging import get_logger
    logger = get_logger(__name__)
    logger.warning("testing to see if log recieved")
    assert "testing to see if log recieved" in caplog.text