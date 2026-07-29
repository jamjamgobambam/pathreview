# Solution Plan — Issue #155

**Issue:** [#155 — Health check references `settings.redis_host`, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)
**Tier:** 1 (`bug`, `api`, `good first issue`)
**Branch:** `fix/155-health-check-redis-config`

---

## 1. Problem Summary

The `/health` endpoint probes three dependencies: PostgreSQL, Redis, and the vector DB.
The Redis probe constructs its client from two settings fields that do not exist:

```python
# api/routes/health.py:44-49
r = redis.Redis(
    host=settings.redis_host,   # <-- not defined on Settings
    port=settings.redis_port,   # <-- not defined on Settings
    db=0,
    decode_responses=True,
)
```

`core/config.py` defines Redis connectivity as a **single URL field**, not host/port:

```python
# core/config.py:12
redis_url: str = Field(default="redis://localhost:6379/0")
```

Accessing `settings.redis_host` therefore raises `AttributeError`.

## 2. Impact

The `AttributeError` is raised inside the `try` block and swallowed by the broad
`except Exception` handler on line 53. The consequences are:

1. **The Redis probe never runs.** `r.ping()` is unreachable — the exception is thrown while
   building the client, one line earlier.
2. **Redis is always reported `"unhealthy"`**, regardless of the actual state of the server.
3. **`/health` always returns HTTP 503.** Line 83 escalates any unhealthy dependency to an
   overall unhealthy status, so the endpoint fails permanently — even on a fully healthy system.
4. **The failure is silent and misleading.** The logged error is an `AttributeError` about a
   config field, not a connection problem, so the log points away from the real cause.

This makes the health check actively harmful: any uptime monitor, load balancer, or container
orchestrator polling `/health` sees the service as permanently down.

## 3. Root Cause

A mismatch between the config schema and its consumer. `Settings` models Redis as a URL
(consistent with `database_url` and `vector_db_url`), but the health route was written against
a host/port shape that was never added to the model.

## 4. Proposed Fix

Use the field that actually exists, via the `redis-py` URL constructor:

```python
r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
```

**Why this approach over adding `redis_host`/`redis_port` to `Settings`:**

- `redis_url` is already defined, already documented in `.env`, and already the project's
  convention for service connection strings (`database_url`, `vector_db_url` follow it).
- Adding host/port fields would create **two competing sources of truth** for the same
  connection — they could drift out of sync, and it is ambiguous which one wins.
- `from_url` parses db index, credentials, and TLS (`rediss://`) from the URL for free. The
  current code hardcodes `db=0`, silently ignoring the `/0` segment of the URL.
- It is a one-line change confined to a single file, matching the Tier-1 scope of the issue.

## 5. Files to Change

| File | Change |
|---|---|
| `api/routes/health.py` | Replace the `redis.Redis(host=…, port=…)` call with `redis.Redis.from_url(settings.redis_url, …)` |
| `tests/unit/test_health.py` | **New file** — unit tests for the health endpoint's Redis probe |

## 6. Test Plan

No `tests/unit/test_health.py` exists today, so this adds one, following the conventions in
`tests/unit/test_review_service.py` (`@pytest.mark.unit` class, `AsyncMock` for the DB session,
`unittest.mock.patch` for external clients).

Cases to cover:

1. **Regression test (fails before the fix):** patch `redis.Redis.from_url` to return a mock
   whose `ping()` succeeds, and assert `dependencies["redis"] == "healthy"`. Before the fix this
   fails, because the `AttributeError` marks Redis unhealthy regardless of the mock.
2. **Config contract:** assert `Settings` exposes `redis_url` and that the probe reads it —
   guards against the same schema/consumer drift reappearing.
3. **Genuine failure still detected:** make `ping()` raise `ConnectionError`; assert Redis is
   reported `"unhealthy"` and the endpoint returns 503. Confirms the fix doesn't mask real outages.
4. **Healthy path:** with all probes mocked healthy, assert HTTP 200 and `status == "healthy"`.

All tests mock the Redis client, so they satisfy the `unit` marker's "no external dependencies"
contract and run without Docker.

## 7. Verification Steps

```bash
make check        # ruff + black + mypy
make test-unit    # unit suite, including the new tests
```

Manual confirmation of the reproduction and the fix:

```bash
# Before: AttributeError -> redis always "unhealthy" -> 503
# After:  probe runs against redis_url and reports the true state
curl -i localhost:8000/health
```

## 8. Out of Scope

- The bare `await db.execute("SELECT 1")` on line 31 (raw SQL string) — that is **issue #154**
  and belongs in its own PR.
- The `safety_events_last_hour` placeholder on line 78 — tracked separately as #D-08.
- Broadening the `except Exception` handlers. Worth doing, but it changes behavior beyond this
  issue's scope and would make the diff harder to review.
