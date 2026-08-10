"""Shared test fixtures for PathReview."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import structlog

if TYPE_CHECKING:
    import logging
    from collections.abc import Callable


def _configure_structlog_for_tests() -> None:
    """Route structlog events through stdlib for pytest log capture."""
    logger_factory: Callable[..., logging.Logger] = structlog.stdlib.LoggerFactory()
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=logger_factory,
        cache_logger_on_first_use=False,
    )


_configure_structlog_for_tests()


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
