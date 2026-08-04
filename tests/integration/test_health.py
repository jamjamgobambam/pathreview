"""Reproduction test for issue #154.

The Postgres probe in api/routes/health.py runs:

    await db.execute("SELECT 1")

SQLAlchemy 2.x no longer implicitly coerces a raw Python string into an
executable SQL construct. Passing a bare string raises:

    sqlalchemy.exc.ArgumentError: Textual SQL expression 'SELECT 1' should be
    explicitly declared as text('SELECT 1')

That ArgumentError is caught by the broad `except Exception` in
health_check(), so instead of GET /health returning 200 with
dependencies.postgres == "healthy", it returns 503 with
dependencies.postgres == "unhealthy" -- a false negative, since the
database itself is reachable and functioning.

This test runs against a real Postgres instance (see the `postgres`
service container in .github/workflows/ci.yml, and `docker-compose.yml`
for local dev), matching how the rest of tests/integration is exercised
in CI. It currently FAILS on main / before the fix. After wrapping the
literal query in sqlalchemy.text(), it should pass.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_reports_postgres_healthy():
    """
    With a real, reachable database, GET /health should report
    dependencies.postgres == "healthy" and an overall 200 status.

    Before the fix: fails because db.execute("SELECT 1") raises
    ArgumentError under SQLAlchemy 2.x, which is caught and reported as
    "unhealthy", causing the endpoint to return 503 instead of 200.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    body = response.json()
    # health_check() raises HTTPException(503, detail=health_status) if ANY
    # dependency is unhealthy, so the payload we want lives under "detail"
    # in that case.
    payload = body["detail"] if response.status_code == 503 else body

    # NOTE: this assertion is scoped to postgres only, on purpose.
    # settings.redis_host / settings.redis_port referenced in the redis
    # check below don't actually exist on Settings (only redis_url does),
    # so the redis check independently raises AttributeError and reports
    # "unhealthy" regardless of this fix. That's a separate bug from #154,
    # so we don't want it to make this reproduction test look unresolved
    # once the postgres fix lands. Overall response.status_code is
    # deliberately NOT asserted here for the same reason.
    assert payload["dependencies"]["postgres"] == "healthy", (
        f"Expected postgres to report healthy, got: "
        f"{payload['dependencies']['postgres']}. This reproduces issue #154: "
        "the raw 'SELECT 1' string passed to db.execute() is not wrapped in "
        "sqlalchemy.text(), so SQLAlchemy 2.x raises ArgumentError and the "
        "health check reports a false failure."
    )
