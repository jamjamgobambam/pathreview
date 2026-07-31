"""Integration tests for issue #86: X-RateLimit-* headers on real responses.

Requires the docker-compose Redis service to be running (`docker compose up -d`).
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.redis import redis_client


@pytest.fixture(autouse=True)
def _clear_rate_limit_keys():
    for key in redis_client.keys("rate_limit:*"):
        redis_client.delete(key)
    yield
    for key in redis_client.keys("rate_limit:*"):
        redis_client.delete(key)


@pytest.mark.integration
def test_response_includes_rate_limit_headers():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "59"


@pytest.mark.integration
def test_remaining_count_decreases_across_requests():
    client = TestClient(app)

    first = client.get("/")
    second = client.get("/")

    first_remaining = int(first.headers["X-RateLimit-Remaining"])
    second_remaining = int(second.headers["X-RateLimit-Remaining"])
    assert second_remaining == first_remaining - 1


@pytest.mark.integration
def test_exceeding_limit_returns_429_with_headers():
    client = TestClient(app)

    for _ in range(60):
        response = client.get("/")
        assert response.status_code == 200

    blocked = client.get("/")

    assert blocked.status_code == 429
    assert blocked.headers["X-RateLimit-Remaining"] == "0"
    assert "X-Request-ID" in blocked.headers


@pytest.mark.integration
def test_health_endpoint_is_excluded_from_rate_limiting():
    client = TestClient(app)

    response = client.get("/health")

    assert "X-RateLimit-Limit" not in response.headers
