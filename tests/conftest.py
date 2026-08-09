"""Shared test fixtures for PathReview."""

import logging

import pytest
import structlog


@pytest.fixture(autouse=True)
def structlog_to_caplog(caplog):
    """Route structlog events into stdlib logging so pytest's ``caplog`` sees them.

    The app only configures structlog at startup (``core.logging.configure_logging``),
    which the test suite never calls. Without it, structlog uses its default
    ``PrintLogger`` and writes straight to stdout, so ``caplog`` — a stdlib logging
    handler — captures nothing and every ``caplog``-based assertion fails even
    though the code under test does emit the expected event.

    This autouse fixture points structlog at ``LoggerFactory`` and ends the
    processor chain with a ``ConsoleRenderer``, so each event is rendered to a
    single string that becomes the stdlib ``LogRecord`` message. Rendering to a
    string (rather than ``render_to_log_kwargs``) is deliberate: the codebase logs
    with bound keys such as ``name`` that collide with reserved ``LogRecord``
    attributes and would raise ``KeyError`` if passed through as ``extra``.
    ``caplog.set_level`` lowers the threshold to DEBUG so INFO/DEBUG events are
    captured too, and defaults are reset after each test so configuration does not
    leak between tests.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )
    caplog.set_level(logging.DEBUG)
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
