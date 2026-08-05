from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.request_id import RequestIDMiddleware


class StubRateLimiter:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def check_rate_limit(self, identifier: str, limit: int, window_seconds: int = 60):
        response = self.responses[self.calls]
        self.calls += 1
        return response


def create_app(rate_limiter):
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware, rate_limiter=rate_limiter)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return app


def test_allowed_response_includes_rate_limit_headers():
    limiter = StubRateLimiter([(True, 59)])
    app = create_app(limiter)
    client = TestClient(app)

    response = client.get("/ping")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "59"


def test_blocked_response_includes_rate_limit_headers():
    limiter = StubRateLimiter([(False, 0)])
    app = create_app(limiter)
    client = TestClient(app)

    response = client.get("/ping")

    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded. Try again later."}
    assert response.headers["X-Request-ID"]
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "0"