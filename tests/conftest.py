"""Shared test fixtures for PathReview."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_user_profile() -> dict[str, Any]:
    """Return the shared sample portfolio fixture as a dict.

    Loads ``tests/fixtures/sample_profiles/basic_profile.json``, which holds a
    ``profile`` object mirroring the columns of :class:`core.models.profile.Profile`
    and a ``repos`` list of two repositories. Use this instead of building profile
    data inline so tests share one consistent sample portfolio.
    """
    fixture_path = FIXTURES_DIR / "sample_profiles" / "basic_profile.json"
    with fixture_path.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


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
