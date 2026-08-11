"""Shared test fixtures for PathReview.

Configures structlog to emit through stdlib logging so pytest's caplog
fixture can capture application log events (issue #159). Production
configure_logging() in core/logging.py is intentionally not used here.
"""

from __future__ import annotations

import logging

import pytest
import structlog


def _configure_structlog_for_tests() -> None:
    """Wire structlog into stdlib logging for the test session.

    Uses LoggerFactory + BoundLogger so events become LogRecords that
    caplog can capture. cache_logger_on_first_use is False so import-time
    loggers pick up this configuration.
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ]
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(format="%(message)s", level=logging.INFO)
    root.setLevel(logging.INFO)


_configure_structlog_for_tests()


@pytest.fixture(autouse=True)
def _ensure_caplog_level(caplog: pytest.LogCaptureFixture) -> None:
    """Keep root/caplog levels at INFO so warnings are always captured."""
    caplog.set_level(logging.INFO)
    logging.getLogger().setLevel(logging.INFO)


@pytest.fixture
def sample_resume_text() -> str:
    """Return a sample resume text for testing."""
    return """
    Jane Doe
    Software Engineer
    jane.doe@example.com | github.com/janedoe

    Experience:
    - Software Engineer at TechCorp (2022-2024)
      Built REST APIs using Python and FastAPI.

    Education:
    - B.S. Computer Science, State University (2022)

    Skills: Python, JavaScript, React, PostgreSQL, Docker
    """


@pytest.fixture
def sample_readme_text() -> str:
    """Return a sample README text for testing."""
    return """
    # Weather App
    A weather forecasting application built with React and OpenWeatherMap API.

    ## Features
    - Current weather display
    - 5-day forecast
    - Location search

    ## Tech Stack
    - React 18
    - TypeScript
    - Tailwind CSS
    - OpenWeatherMap API
    """
