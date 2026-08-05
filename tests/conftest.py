"""Shared test fixtures for PathReview."""

import logging
from collections.abc import Iterator

import pytest
import structlog


@pytest.fixture(autouse=True)
def configure_structlog_for_tests() -> Iterator[None]:
    """Route structlog events through stdlib ``logging`` so pytest's ``caplog``
    can capture them.

    By default structlog uses ``PrintLogger``, which writes rendered events
    straight to stdout and never touches stdlib ``logging``. Since ``caplog``
    only sees records that flow through stdlib ``logging``, log-based
    assertions would always fail. Configuring a ``stdlib.LoggerFactory`` with a
    plain (non-ANSI) renderer fixes this for every test.
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
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
    # Ensure WARNING-level records propagate to caplog's handler.
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
