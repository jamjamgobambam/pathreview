"""Regression tests for issue #155.

Originally the health check built its Redis probe with
``redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)``, but
``Settings`` (``core/config.py``) only defines ``redis_url`` -- no ``redis_host``
or ``redis_port``. Evaluating ``settings.redis_host`` raised ``AttributeError``,
which the probe's ``try/except Exception`` swallowed, so ``GET /health`` *always*
reported Redis ``"unhealthy"`` and returned HTTP 503 even when Redis was
reachable.

The fix probes Redis via ``redis.Redis.from_url(settings.redis_url, ...)`` -- the
single source of truth already on ``Settings``.

These tests stub the ``redis`` module so no live server is required:

* ``test_health_reports_redis_healthy_when_reachable`` -- Redis pings fine, so
  ``/health`` must return 200 with redis ``"healthy"``. This FAILED before the
  fix (503 / "unhealthy") and now passes -- it is the direct reproduction of #155.
* ``test_health_reports_redis_unhealthy_when_unreachable`` -- Redis ping raises,
  so ``/health`` must still report ``"unhealthy"`` / 503. This guards against a
  fix that "passes" by never actually checking Redis.

Issue: https://github.com/ascherj/pathreview/issues/155
"""

import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.health import router
from core.database import get_db


def _install_fake_redis(monkeypatch, *, reachable):
    """Install a stub ``redis`` module whose client ping reflects ``reachable``.

    Supports both ``Redis(...)`` and ``Redis.from_url(...)`` construction so the
    test is agnostic to how the health check builds its client.
    """
    fake_redis = types.ModuleType("redis")

    class _FakeRedis:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        @classmethod
        def from_url(cls, url, **kwargs):
            return cls(url, **kwargs)

        def ping(self):
            if not reachable:
                raise ConnectionError("Error connecting to Redis")
            return True

    fake_redis.Redis = _FakeRedis
    monkeypatch.setitem(sys.modules, "redis", fake_redis)


@pytest.fixture
def make_client(monkeypatch):
    """Return a factory building a /health test client with a stubbed Redis + DB."""

    def _make(*, redis_reachable):
        _install_fake_redis(monkeypatch, reachable=redis_reachable)

        class _FakeDB:
            async def execute(self, *args, **kwargs):
                return None

        async def _fake_get_db():
            yield _FakeDB()

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = _fake_get_db
        return TestClient(app)

    return _make


def _dependencies(resp):
    """Unwrap the dependencies dict from a 200 body or a 503 ``detail`` body."""
    body = resp.json()
    return body.get("detail", body)["dependencies"]


@pytest.mark.unit
def test_health_reports_redis_healthy_when_reachable(make_client):
    """With Redis reachable, /health returns 200 and redis 'healthy' (repro #155)."""
    resp = make_client(redis_reachable=True).get("/health")

    assert _dependencies(resp)["redis"] == "healthy", (
        "Redis is reachable (ping succeeds) but the health check reports it "
        "unhealthy -- issue #155 (settings.redis_host does not exist)."
    )
    assert resp.status_code == 200


@pytest.mark.unit
def test_health_reports_redis_unhealthy_when_unreachable(make_client):
    """With Redis down, /health must still report redis 'unhealthy' and 503."""
    resp = make_client(redis_reachable=False).get("/health")

    assert _dependencies(resp)["redis"] == "unhealthy"
    assert resp.status_code == 503
