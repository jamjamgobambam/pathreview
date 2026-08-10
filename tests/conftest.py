"""Shared test fixtures for PathReview."""

import pytest
import structlog


@pytest.fixture(autouse=True)
def configure_structlog_for_tests() -> None:
    """Bridge structlog output into stdlib `logging` so `caplog` sees it.

    Without this, `structlog.get_logger()` falls back to structlog's own
    default global configuration, which renders events straight to stdout
    through its own processor chain and never reaches the stdlib root logger
    that pytest's `caplog` fixture attaches to (issue #159). Configuring
    `logger_factory=structlog.stdlib.LoggerFactory()` here — mirroring the
    real `configure_logging()` in `core/logging.py`, which is only ever
    called from `scripts/seed_db.py` and never during tests — routes every
    `structlog.get_logger()` call through a real `logging.Logger`, so
    `caplog.text` / `caplog.records` work for any test.

    Function-scoped (not session-scoped) and `cache_logger_on_first_use=False`
    so this reconfigures on every test and never lets a module-level
    `logger = structlog.get_logger()` cache a stale configuration.
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
            structlog.processors.KeyValueRenderer(key_order=["event"]),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )


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
