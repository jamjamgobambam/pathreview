from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.rate_limit import RateLimitMiddleware


def create_test_app(rate_limiter, limit=60):
    """Create a test app with rate limit middleware."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/")
    async def test_route():
        return {"message": "ok"}

    return app


def test_allowed_response_includes_rate_limit_headers(monkeypatch):
    """Allowed responses should include rate limit headers."""
    mock_limiter = Mock()
    mock_limiter.check_rate_limit.return_value = (True, 59)

    monkeypatch.setattr(
        "api.middleware.rate_limit.RateLimiter",
        lambda redis_client: mock_limiter,
    )

    client = TestClient(create_test_app(mock_limiter))

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "59"


def test_rate_limit_exceeded_returns_429(monkeypatch):
    """Requests over the limit should return 429 with rate limit headers."""
    mock_limiter = Mock()
    mock_limiter.check_rate_limit.return_value = (False, 0)

    monkeypatch.setattr(
        "api.middleware.rate_limit.RateLimiter",
        lambda redis_client: mock_limiter,
    )

    client = TestClient(create_test_app(mock_limiter))

    response = client.get("/")

    assert response.status_code == 429
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.json() == {"detail": "Rate limit exceeded"}
