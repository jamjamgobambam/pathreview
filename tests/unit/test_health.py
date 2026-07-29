"""Reproduction tests for issue #155.

Issue: https://github.com/ascherj/pathreview/issues/155
`api/routes/health.py` builds its Redis client from `settings.redis_host` and
`settings.redis_port`, but `core/config.py` only defines `redis_url`. Accessing
the missing attributes raises `AttributeError`, which the health handler catches
and reports as an unhealthy Redis dependency — so `GET /health` returns 503 even
when Redis is actually reachable.

`test_settings_is_missing_redis_host_and_port` documents the root cause and
passes on the buggy code. `test_health_reports_redis_healthy_when_reachable`
documents the user-facing impact and is expected to FAIL until the Week 9 fix
builds the client from `redis_url`.
"""

import pytest

pytestmark = pytest.mark.unit


def test_settings_is_missing_redis_host_and_port():
    """Root cause: Settings exposes redis_url but not redis_host / redis_port."""
    from core.config import settings

    assert settings.redis_url  # the field that actually exists
    with pytest.raises(AttributeError):
        _ = settings.redis_host
    with pytest.raises(AttributeError):
        _ = settings.redis_port


def _make_client(monkeypatch):
    """Build a TestClient for the health router with the DB and Redis stubbed
    so the only thing under test is the Redis-probe wiring."""
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
            return True

    # Stub both construction paths so no real network call is ever made:
    # the current (buggy) code uses redis.Redis(...); the fix will use from_url(...).
    monkeypatch.setattr(redis.Redis, "from_url", lambda *a, **k: _FakeRedis())
    monkeypatch.setattr(redis, "Redis", lambda *a, **k: _FakeRedis())

    app = FastAPI()
    app.include_router(router)

    async def _override_get_db():
        yield _FakeDB()

    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


def test_health_reports_redis_healthy_when_reachable(monkeypatch):
    """With a reachable Redis, GET /health should return 200 and redis healthy.

    EXPECTED TO FAIL on current code (issue #155): the AttributeError from
    settings.redis_host is caught and Redis is reported unhealthy, so the
    endpoint returns 503. The Week 9 fix makes this pass.
    """
    client = _make_client(monkeypatch)
    resp = client.get("/health")

    assert resp.status_code == 200, resp.text
    assert resp.json()["dependencies"]["redis"] == "healthy"
