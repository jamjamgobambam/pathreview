"""Shared test fixtures for PathReview."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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


@pytest.fixture
def basic_profile() -> dict[str, Any]:
    """Load the shared sample portfolio fixture.

    Returns the parsed contents of
    ``tests/fixtures/sample_profiles/basic_profile.json`` — a realistic sample
    portfolio (GitHub username, resume text, and two repositories) used by
    integration tests to drive the ingestion pipeline.
    """
    fixture_path = FIXTURES_DIR / "sample_profiles" / "basic_profile.json"
    data: dict[str, Any] = json.loads(fixture_path.read_text())
    return data
