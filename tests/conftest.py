"""Shared test fixtures for PathReview.

Reproduction note (issue #159): structlog output is not bridged into stdlib
`logging`, so pytest's `caplog` fixture never sees it. No fixture here
configures `structlog.configure(...)` for the test process, so log calls made
via `structlog.get_logger()` (e.g. `ingestion/embeddings/batch_processor.py`)
render straight to stdout through structlog's own processor chain and never
reach the stdlib root logger that `caplog` attaches to.

Repro steps:
    .venv/Scripts/python.exe -m pytest \
        tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::\
test_empty_chunks_list_returns_empty -q

Observed: the test fails with `AssertionError: assert ('Empty chunks list' in
'' or False)` — `caplog.text` is empty even though "Captured stdout call"
shows the line was logged:
    2026-07-24 04:17:08 [warning  ] Empty chunks list provided to BatchEmbeddingProcessor

Fix (tracked in PLAN.md): add a fixture here that routes structlog through
`structlog.stdlib.ProcessorFormatter` (or wraps tests in
`structlog.testing.capture_logs()`) so `caplog`-based assertions work
suite-wide, not just for this one test.
"""

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
