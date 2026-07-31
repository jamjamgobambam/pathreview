"""Shared test fixtures for PathReview."""

from collections.abc import Iterator

import pytest
import structlog


@pytest.fixture(autouse=True)
def configure_structlog_for_caplog() -> Iterator[None]:
    """Route structlog events through stdlib logging so pytest's ``caplog`` captures them.

    The application configures structlog with a stdlib ``LoggerFactory`` at startup
    (see ``core.logging.configure_logging``), but that is never called during tests.
    Without it, structlog falls back to its default ``PrintLogger`` and writes straight
    to stdout/stderr, bypassing the stdlib ``logging`` system that ``caplog`` observes.

    This autouse fixture configures structlog to emit real stdlib ``LogRecord``s via
    ``render_to_log_kwargs`` and disables logger caching so module-level loggers that
    were bound at import time pick up this configuration.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
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
