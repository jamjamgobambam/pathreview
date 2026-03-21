"""Shared test fixtures for PathReview."""

import pytest


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
