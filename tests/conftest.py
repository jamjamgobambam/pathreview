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


@pytest.fixture
def sample_workflow_yaml() -> str:
    """Return a sample GitHub Actions workflow YAML for testing."""
    return """
    name: CI
    on:
      push:
        branches: [main]
      pull_request: {}
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
          - run: pip install -r requirements.txt
          - run: pytest
      deploy:
        runs-on: ubuntu-latest
        needs: test
        steps:
          - uses: docker/build-push-action@v5
          - run: ./deploy.sh production
    """
