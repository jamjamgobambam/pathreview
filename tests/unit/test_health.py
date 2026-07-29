"""Tests for the /health endpoint's Redis probe (issue #155).

Issue: https://github.com/ascherj/pathreview/issues/155
`api/routes/health.py` previously built its Redis client from
`settings.redis_host` / `settings.redis_port`, but `core/config.py` only defines
`redis_url`. Accessing the missing attributes raised `AttributeError`, which the
handler caught and reported as an unhealthy Redis dependency — so `GET /health`
returned 503 even when Redis was reachable. The fix builds the client from
`settings.redis_url` via `redis.Redis.from_url(...)`.

These tests lock in the fixed behavior: the healthy path reports Redis healthy
(200), and the unreachable path reports Redis unhealthy (503).
"""

import pytest

pytestmark = pytest.mark.unit


def test_settings_exposes_redis_url_used_by_health_check():
    """The health check must read a Settings field that actually exists.

    Guards against a regression to the #155 bug, where the handler read
    redis_host / redis_port, which Settings never defined.
    """
    from core.config import settings

    assert settings.redis_url
    assert not hasattr(settings, "redis_host")
    assert not hasattr(settings, "redis_port")


def _make_client(monkeypatch, ping):
    """Build a TestClient for the health router with the DB stubbed healthy and
    Redis stubbed to run ``ping`` (a callable that returns True or raises)."""
    import redis
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api.routes.health import router
    from core.database import get_db

    class _FakeDB:
        async def execute(self, *args, **kwargs):
            return None

    class _FakeRedis:
        def ping(self):
            return ping()

    captured = {}

    def _fake_from_url(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return _FakeRedis()

    monkeypatch.setattr(redis.Redis, "from_url", _fake_from_url)

    app = FastAPI()
    app.include_router(router)

    async def _override_get_db():
        yield _FakeDB()

    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app), captured


def test_health_reports_redis_healthy_when_reachable(monkeypatch):
    """Reachable Redis -> 200 with redis healthy, built from redis_url."""
    from core.config import settings

    client, captured = _make_client(monkeypatch, ping=lambda: True)
    resp = client.get("/health")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dependencies"]["redis"] == "healthy"
    assert body["status"] == "healthy"
    # Client is constructed from the configured URL, not host/port.
    assert captured["url"] == settings.redis_url
    assert captured["kwargs"].get("decode_responses") is True


def test_health_reports_redis_unhealthy_when_unreachable(monkeypatch):
    """Redis ping failure -> redis unhealthy and overall 503 (error is caught)."""

    def _boom():
        raise ConnectionError("connection refused")

    client, _ = _make_client(monkeypatch, ping=_boom)
    resp = client.get("/health")

    assert resp.status_code == 503, resp.text
    detail = resp.json()["detail"]
    assert detail["dependencies"]["redis"] == "unhealthy"
    assert detail["status"] == "unhealthy"
