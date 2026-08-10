"""Shared test fixtures for PathReview."""

import logging
from collections.abc import Iterator

import pytest
import structlog


@pytest.fixture(autouse=True)
def configure_structlog_for_caplog() -> Iterator[None]:
    """Route structlog through stdlib logging so pytest's caplog can capture it.

    Application code logs with ``structlog.get_logger()``. Without a stdlib
    ``LoggerFactory``, those events print to stdout and never become
    ``logging.LogRecord``s, so ``caplog.text`` / ``caplog.records`` stay empty.
    This test-only config mirrors the stdlib integration in
    ``core.logging.configure_logging`` without changing production logging.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Render to a string, then hand off to the stdlib logger so caplog
            # receives a real LogRecord whose message includes the event text.
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # Avoid caching so module-level get_logger() proxies pick up this config.
        cache_logger_on_first_use=False,
    )
    # Ensure warning-level events are not filtered before reaching caplog.
    logging.getLogger().setLevel(logging.DEBUG)
    yield
    structlog.reset_defaults()


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
