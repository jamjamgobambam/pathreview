"""Tests for api/routes/health.py.

Focuses on issue #154: the postgres probe must correctly report the database
as healthy when it is reachable. Prior to the fix, the probe passed a bare
"SELECT 1" string to AsyncSession.execute(), which SQLAlchemy 2.x rejects,
so the probe silently reported "unhealthy" on every request.

The redis probe is intentionally not covered here — a separate bug (#155)
causes it to always report unhealthy regardless of Redis state, and that
issue is out of scope for this PR.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient wrapping the real FastAPI app.

    The health endpoint depends on a live Postgres connection via
    core.database.get_db, so this test requires the Docker services
    (docker compose up -d) to be running before it is executed.
    """
    return TestClient(app)


@pytest.mark.unit
def test_health_check_postgres_reports_healthy(client: TestClient) -> None:
    """GET /health should mark postgres as 'healthy' when the DB is reachable.

    Regression test for issue #154. Before the fix, the postgres probe used a
    raw SQL string (`await db.execute("SELECT 1")`), which SQLAlchemy 2.x
    rejects with ArgumentError. The exception was caught by the endpoint's
    try/except and reported as 'unhealthy' even when Postgres was up. The fix
    wraps the query in sqlalchemy.text().
    """
    response = client.get("/health")

    # The endpoint returns 200 when every probed dependency is healthy, and
    # 503 (with the same JSON body under `detail`) when any dependency is
    # unhealthy. We inspect the dependencies map either way, because the redis
    # probe has an unrelated bug (#155) that can flip the top-level status.
    if response.status_code == 200:
        payload = response.json()
    else:
        assert (
            response.status_code == 503
        ), f"Expected 200 or 503 from /health, got {response.status_code}"
        payload = response.json()["detail"]

    assert payload["dependencies"]["postgres"] == "healthy", (
        "Postgres probe should report healthy when the DB is reachable. " f"Full payload: {payload}"
    )
