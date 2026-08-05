"""Regression test for issue #154: health check DB probe must use sqlalchemy.text()."""

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_reports_postgres_healthy_when_reachable() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    body = response.json()
    dependencies = body.get("dependencies") or body["detail"]["dependencies"]

    assert dependencies["postgres"] == "healthy"
