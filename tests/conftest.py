"""Shared test fixtures for PathReview."""

import os

import pytest

_postgres_container = None
_redis_container = None


def _should_start_test_containers(config: pytest.Config) -> bool:
    """Skip the containers when the run is explicitly unit-only."""
    markexpr = config.getoption("markexpr", default="") or ""
    return markexpr.strip() not in ("unit", "not integration")


def _start_postgres_container() -> None:
    """Start an ephemeral Postgres container for integration tests.

    core/database.py builds its async engine from settings.database_url at
    import time, so DATABASE_URL must be set before core.database (or
    anything that imports it) is imported anywhere in the process. This hook
    runs during pytest's early configure phase, before any test module is
    collected/imported, which is the only place that ordering is guaranteed.
    """
    global _postgres_container

    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError as exc:
        print(
            f"\n[conftest] Skipping Postgres testcontainer: "
            f"testcontainers[postgres] not installed ({exc})"
        )
        return

    container = PostgresContainer("postgres:16-alpine", driver="asyncpg")
    try:
        container.start()
    except Exception as exc:  # Docker not installed/running
        print(f"\n[conftest] Skipping Postgres testcontainer: {exc}")
        return

    _postgres_container = container
    os.environ["DATABASE_URL"] = container.get_connection_url()

    # Build the schema via the real Alembic migrations rather than
    # Base.metadata.create_all() -- alembic/env.py reads settings.database_url
    # directly, so it picks up the container URL set above. This deliberately
    # exercises the same migration path used in dev/prod instead of the ORM's
    # own DDL generation.
    #
    # Shelled out rather than `from alembic import command`: pytest puts the
    # repo root on sys.path, and this project's own alembic/ directory (env.py,
    # versions/) shadows the installed alembic package at that point. The
    # venv's alembic console script doesn't have that problem since its
    # sys.path[0] is the script's own directory, not the cwd.
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    alembic_bin = Path(sys.executable).parent / "alembic"
    subprocess.run(
        [str(alembic_bin), "upgrade", "head"],
        cwd=str(repo_root),
        env=os.environ,
        check=True,
    )


def _start_redis_container() -> None:
    """Start an ephemeral Redis container for integration tests.

    core/redis_client.py builds its async client from settings.redis_url at
    import time (same pattern as core/database.py's engine), so REDIS_URL
    must be set before core.redis_client (or core.config) is imported
    anywhere in the process -- same ordering constraint as the Postgres
    container above, which is why this also runs from pytest_configure.
    """
    global _redis_container

    try:
        from testcontainers.redis import RedisContainer
    except ImportError as exc:
        print(
            f"\n[conftest] Skipping Redis testcontainer: "
            f"testcontainers[redis] not installed ({exc})"
        )
        return

    container = RedisContainer("redis:7-alpine")
    try:
        container.start()
    except Exception as exc:  # Docker not installed/running
        print(f"\n[conftest] Skipping Redis testcontainer: {exc}")
        return

    _redis_container = container
    host = container.get_container_host_ip()
    port = container.get_exposed_port(6379)
    os.environ["REDIS_URL"] = f"redis://{host}:{port}/0"
    print(f"\n[conftest] Redis testcontainer started at {host}:{port}")


def pytest_configure(config: pytest.Config) -> None:
    """Pytest hook: start the ephemeral Postgres/Redis containers, if needed."""
    if not _should_start_test_containers(config):
        return

    _start_postgres_container()
    _start_redis_container()


def pytest_unconfigure(config: pytest.Config) -> None:
    """Pytest hook: stop any containers started by pytest_configure."""
    if _postgres_container is not None:
        _postgres_container.stop()
    if _redis_container is not None:
        _redis_container.stop()


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
