"""Integration regression test for issue #155.

api/routes/health.py used to probe Redis using settings.redis_host and
settings.redis_port, but Settings (core/config.py) only defines redis_url.
That mismatch raised an AttributeError inside the health check's Redis probe,
so /health reported Redis as unhealthy even when Redis was up and reachable
(see docker-compose.yml's redis service). The fix builds the client from
settings.redis_url instead, so this test confirms /health now correctly
reports Redis as healthy when the real Redis container is reachable.
Requires the docker-compose `redis` service to be running.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.integration
def test_health_reports_redis_healthy_when_redis_is_up():
    with TestClient(app) as client:
        response = client.get("/health")

    body = response.json()
    dependencies = body.get("dependencies") or body.get("detail", {}).get("dependencies", {})

    assert dependencies.get("redis") == "healthy"
