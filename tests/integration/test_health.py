"""Reproduction test for issue #155.

api/routes/health.py probes Redis using settings.redis_host and
settings.redis_port, but Settings (core/config.py) only defines redis_url.
That mismatch raises an AttributeError inside the health check's Redis probe,
so /health reports Redis as unhealthy even when Redis is up and reachable
(see docker-compose.yml's redis service). This test expects the health check
to correctly report Redis as healthy and currently fails because of the bug.
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
