"""Shared test fixtures for PathReview."""

from collections.abc import Iterator

import pytest
import structlog


@pytest.fixture(autouse=True)
def configure_structlog_for_tests() -> Iterator[None]:
    """Route structlog events through stdlib logging so ``caplog`` can capture them.

    ``configure_logging()`` is never called during tests, so structlog falls back to
    its default ``PrintLoggerFactory``, which writes straight to stdout and bypasses
    the stdlib ``logging`` module that pytest's ``caplog`` fixture hooks into. That is
    why log assertions saw an empty ``caplog.text`` while the event showed up in
    captured stdout.

    ``render_to_log_kwargs`` is the final processor so the event string arrives as the
    record's ``msg`` (a clean ``record.message``) and the bound key/values land in
    ``extra``; the record's level comes from the stdlib method structlog dispatches to.

    ``cache_logger_on_first_use`` must stay ``False``: modules bind their logger at
    import time (e.g. ``ingestion/embeddings/batch_processor.py``), so a cached logger
    would freeze whatever factory was active at first use and ignore this fixture.
    """
    structlog.configure(
        processors=[structlog.stdlib.render_to_log_kwargs],
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
