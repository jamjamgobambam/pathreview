"""Shared test fixtures for PathReview."""

import pytest
import structlog


@pytest.fixture(autouse=True)
def structlog_to_stdlib_logging():
    """Route structlog output through the stdlib ``logging`` pipeline for tests.

    The application only wires structlog into standard-library logging inside
    ``core.logging.configure_logging()``, which is called solely by
    ``scripts/seed_db.py`` — never by the app under test or the test suite. With
    structlog left at its default configuration during tests, it renders events
    straight to stdout and never produces ``logging.LogRecord`` objects, so
    pytest's ``caplog`` fixture captures nothing and every log-based assertion
    fails suite-wide (issue #159).

    This autouse fixture reconfigures structlog so its final processor,
    ``structlog.stdlib.render_to_log_kwargs``, hands each event and its bound
    key/values to a stdlib logger created by ``LoggerFactory``. That produces
    real ``LogRecord`` objects that propagate to the handler ``caplog`` installs
    per test. ``cache_logger_on_first_use=False`` ensures module-level loggers
    bound at import time (e.g. ``logger = structlog.get_logger()``) pick up this
    configuration on their next call rather than a cached default logger.
    ``structlog.reset_defaults()`` runs on teardown so configuration never leaks
    between tests.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.render_to_log_kwargs,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
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
