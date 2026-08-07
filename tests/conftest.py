"""Shared test fixtures for PathReview."""

from collections.abc import Iterator

import pytest
import structlog


@pytest.fixture(autouse=True)
def configure_structlog_for_tests() -> Iterator[None]:
    """Route structlog events through stdlib logging so ``caplog`` can capture them.

    structlog's shipped default ``PrintLoggerFactory`` writes rendered events
    straight to stdout and never creates a ``logging.LogRecord``. pytest's
    ``caplog`` fixture is a stdlib logging handler, so it never sees those
    events. Binding ``structlog.stdlib.LoggerFactory`` makes structlog emit
    through ``logging.getLogger(name)`` instead, which is what ``caplog`` reads.

    Two deliberate choices:

    * ``structlog.stdlib.filter_by_level`` is omitted from the chain. It checks
      the stdlib logger's effective level *before* the record is emitted, which
      would discard INFO and DEBUG events even after a test called
      ``caplog.set_level(logging.INFO)`` — reproducing the original "log fires
      but caplog is empty" symptom for a different reason.
    * ``cache_logger_on_first_use`` is ``False`` so that module-level loggers,
      which are created at import time during collection, resolve this
      configuration on use rather than freezing an earlier one.

    The root logger keeps its default WARNING level: a test asserting on INFO or
    DEBUG output must opt in with ``caplog.set_level`` or ``caplog.at_level``.

    Yields:
        None. Configuration is reset after each test so that this
        process-global setup cannot leak into unrelated tests.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        context_class=dict,
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
