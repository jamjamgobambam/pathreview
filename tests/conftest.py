"""Shared test fixtures for PathReview."""

import json
from pathlib import Path
from typing import Any

import pytest

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_profile() -> dict[str, Any]:
    """Return the shared sample profile dict loaded from basic_profile.json.

    The returned dict mirrors the Profile ORM fields (id, user_id,
    github_username, resume_filename, resume_text, portfolio_url) plus a
    supplemental 'repos' list that is not stored in the Profile table.
    """
    fixture_path = _FIXTURES_DIR / "sample_profiles" / "basic_profile.json"
    with fixture_path.open() as f:
        data: dict[str, Any] = json.load(f)
    return data


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
