"""Shared test fixtures for PathReview."""

import pytest
import structlog


@pytest.fixture(autouse=True)
def route_structlog_to_stdlib():
    """Make structlog records visible to pytest's ``caplog`` fixture.

    By default structlog uses a ``PrintLogger`` that writes straight to stdout,
    bypassing the standard-library ``logging`` handlers that ``caplog`` installs.
    Any test asserting on logs via ``caplog`` therefore captures nothing, which
    fails log assertions suite-wide (issue #159).

    Configuring structlog to use the stdlib ``LoggerFactory`` routes every record
    through ``logging`` so ``caplog.records`` / ``caplog.text`` see them.
    ``cache_logger_on_first_use=False`` ensures module-level loggers (bound at
    import time, before this fixture runs) pick up this configuration rather than
    a stale cached default. Defaults are restored after each test.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=False),
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
