# Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings (#155)](https://github.com/ascherj/pathreview/issues/155)

> **Status (Week 9): implemented via the preferred approach.** `api/routes/health.py`
> now probes Redis with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
> Confirmed no other module reads `redis_host`/`redis_port` (grep). Regression test
> [tests/unit/test_health_redis_config.py](tests/unit/test_health_redis_config.py)
> now passes (healthy Redis → 200) and a companion case asserts a down Redis still
> yields `unhealthy`/503. Verified in a clean venv: no new unit-test/lint failures.

### Understand

**Root cause.** `api/routes/health.py` builds its Redis probe with
`redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`, but the
`Settings` model in `core/config.py` never defines `redis_host` or `redis_port`.
It only exposes Redis through a single `redis_url` field
(`redis://localhost:6379/0`). Accessing `settings.redis_host` therefore raises
`AttributeError`.

**Expected vs. actual.**
- *Expected:* `GET /health` pings Redis using the configured connection and
  reports `redis: "healthy"` (HTTP 200) when Redis is reachable, `redis:
  "unhealthy"` (HTTP 503) only when it is genuinely down.
- *Actual:* The `AttributeError` is caught by the probe's `try/except Exception`,
  so the endpoint does not crash — instead it *always* reports `redis:
  "unhealthy"` and returns **HTTP 503**, even when Redis is up. Readiness/liveness
  monitoring can never see the service as healthy.

  (This refines the Week 7 description: the error is swallowed, not raised to the
  caller. The real-world impact is a permanent false-negative 503, not a 500.)

### Map

Files/functions involved:

- **`api/routes/health.py`** → `health_check()` — the Redis probe block that
  reads `settings.redis_host` / `settings.redis_port`. **Primary file to change.**
- **`core/config.py`** → `Settings` — defines `redis_url` but no host/port.
  Only touched if we go with the "add fields" approach (see Plan).
- **`tests/unit/test_health_redis_config.py`** — new reproduction test (already
  added this week); becomes the regression test after the fix.

### Plan

**Preferred approach — probe from the existing `redis_url` (single source of truth):**

1. In `health_check()`, replace
   `redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)`
   with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
2. Confirm no other module reads `settings.redis_host` / `redis_port`
   (`grep -rn "redis_host\|redis_port"`), so the removal is safe.
3. Run `tests/unit/test_health_redis_config.py` — it should now pass (redis
   `healthy` / HTTP 200 when reachable).
4. Add/keep a second assertion that Redis is reported `unhealthy` when `ping()`
   raises, so the fix doesn't accidentally mark a down Redis as healthy.

**Alternative approach (if maintainer prefers explicit fields):** add
`redis_host: str = "localhost"` and `redis_port: int = 6379` to `Settings`. Simpler
diff, but introduces a second source of truth alongside `redis_url` that can drift
— I'll propose approach #1 first and fall back if requested.

### Inputs & outputs

- **Input:** the application `Settings` (specifically the Redis connection config)
  and the live Redis server's reachability.
- **Output / change:** `GET /health` returns a JSON payload whose
  `dependencies.redis` is `"healthy"` (HTTP 200) when Redis responds to `ping()`
  and `"unhealthy"` (HTTP 503) when it does not — driven by real reachability
  rather than a config `AttributeError`. No change to the response schema.

### Risks & unknowns

- **`decode_responses` / client options** — `from_url` must preserve the same
  options the old call used; verify the ping path behaves identically.
- **Other consumers** — need to confirm nothing else depends on `redis_host`
  existing (grep first).
- **`redis_url` format assumptions** — `from_url` should handle the default
  `redis://host:port/db`; confirm auth'd URLs (`redis://:pass@host`) also work if
  the deployment uses them.
- **Test environment** — the project `.venv` was broken locally (Intel wheels vs.
  arm64); reproduction was verified in a clean arm64 Python 3.11 venv. Need the
  project venv rebuilt before running the full suite. (Open question for Week 9.)

### Edge cases

- Redis **down / connection refused** → `redis: "unhealthy"`, HTTP 503 (still
  works, must not regress).
- Redis **URL with auth or non-default db** (`redis://:pass@host:6379/1`) →
  probe still connects.
- **Missing / empty `redis_url`** → probe fails gracefully as `unhealthy`, not an
  unhandled crash.
- The other dependencies (Postgres, vector DB) must be unaffected by the change.
