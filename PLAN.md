## Solution plan

**Issue:** [#155 — Health check references settings.redis_host, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

### Understand
`api/routes/health.py` builds a synchronous Redis client for its health probe using
`settings.redis_host` and `settings.redis_port` (lines 45-46). The `Settings` model in
`core/config.py` never defines those two fields — it only defines a single
`redis_url: str = "redis://localhost:6379/0"` field (line 12).

- **Expected behavior:** `GET /health` connects to Redis using the configured URL and
  reports `"healthy"` or `"unhealthy"` based on whether the `PING` actually succeeds.
- **Actual behavior:** every call to the Redis probe raises `AttributeError:
  'Settings' object has no attribute 'redis_host'` before a client is ever constructed.
  That error is caught by the surrounding bare `except Exception` (health.py:53-56), so
  it never surfaces to the caller as a crash — but it means Redis is unconditionally
  reported `"unhealthy"`, and `health_status["status"]` is forced to `"unhealthy"`,
  which makes the endpoint return `503` regardless of whether Redis is actually up.
  Confirmed locally: instantiating `Settings()` and accessing `.redis_host` raises
  `AttributeError`, and running the exact try/except block from `health.py` swallows
  that error and always sets `redis: unhealthy` (see reproduction commit).

### Map
Files/functions involved:
- `api/routes/health.py` — `health_check()`, specifically the Redis probe block
  (lines 39-56). This is the only place `redis_host`/`redis_port` are referenced in
  the codebase (confirmed via `grep -rn "redis_host\|redis_port" core api`).
- `core/config.py` — `Settings` class (lines 7-49), which defines `redis_url` but not
  `redis_host`/`redis_port`.
- `tests/unit/test_health.py` — new reproduction test added this week; will need a
  companion test for the fixed behavior (e.g. mocking `redis.Redis.from_url` /
  `.ping()` to verify a real "healthy"/"unhealthy" result is returned instead of an
  always-unhealthy fallback).

### Plan
1. Update `api/routes/health.py` to build the Redis client from `settings.redis_url`
   via `redis.Redis.from_url(settings.redis_url, decode_responses=True)` instead of
   passing `host=settings.redis_host, port=settings.redis_port`.
2. Remove the now-unnecessary `db=0` keyword (the DB index is already encoded in
   `redis_url`, e.g. `redis://localhost:6379/0`) to avoid conflicting/duplicate config.
3. Add a unit test in `tests/unit/test_health.py` (or a new integration test using
   `TestClient` + `unittest.mock.patch`) that mocks `redis.Redis.from_url` to confirm
   the probe reports `"healthy"` when `ping()` succeeds and `"unhealthy"` when it
   raises, proving the status now reflects Redis's real state instead of always
   failing.
4. Manually verify against a real Redis instance: start Redis locally (e.g.
   `docker run -p 6379:6379 redis` or `redis-server`), hit `GET /health`, and confirm
   `dependencies.redis == "healthy"`; then stop Redis and confirm it flips to
   `"unhealthy"` with a `503`.
5. Update the reproduction test added in `tests/unit/test_health.py` this week
   (`test_health_redis_probe_raises_attribute_error`) so it no longer asserts the
   broken behavior — replace/retire it once the fix lands, so the test suite reflects
   the corrected contract rather than the bug.

### Inputs & outputs
- **Input:** `settings.redis_url` (a `redis://host:port/db` connection string already
  defined on `Settings`, sourced from env var `REDIS_URL` or `.env`). No new
  environment variables or config fields are introduced.
- **Output:** `health_status["dependencies"]["redis"]` changes from being
  *unconditionally* `"unhealthy"` to accurately reflecting whether `PING` against the
  URL in `redis_url` succeeds (`"healthy"`) or fails (`"unhealthy"`). This also affects
  `health_status["status"]` and the endpoint's HTTP status code (`200` vs `503`), since
  those are derived from the per-dependency results.

### Risks & unknowns
- **`redis.Redis.from_url` option compatibility:** need to confirm no other kwargs
  (e.g. `socket_timeout`) were implicitly relied upon elsewhere — currently none are
  set, so this should be low risk, but worth double-checking `api/routes/health.py`
  for any other Redis usage patterns in the codebase (`grep -rn "redis\." api core`)
  before assuming this is the only call site.
- **No test currently exercises `GET /health` end-to-end:** `tests/integration/` has
  no existing test that boots the app and hits `/health` with `TestClient`, and the
  app's startup lifespan also requires a reachable Postgres (confirmed while trying to
  boot `uvicorn api.main:app` locally without Postgres running — it fails at startup
  before `/health` is ever reachable). Need to decide whether to mock `get_db` and
  Postgres for a true end-to-end test, or keep the fix verified at the unit level only.
- **Bare `except Exception` masks other bugs:** the existing broad exception handling
  in `health.py` is what let this bug ship silently in the first place. Not in scope
  to redesign error handling, but worth flagging — a narrower except or added logging
  detail (e.g. `exc_info=True`) could prevent similar regressions, and is worth raising
  as a follow-up rather than bundling into this fix.

### Edge cases
- **Redis URL with no explicit DB index** (e.g. `redis://localhost:6379`, no trailing
  `/0`) — `from_url` should default correctly; confirm no crash or wrong-db surprises.
- **Redis reachable but `PING` denied** (e.g. `NOAUTH` error from a Redis instance
  requiring a password not present in `redis_url`) — should be caught by the existing
  `except Exception` and reported `"unhealthy"`, not crash the endpoint.
- **Redis completely unreachable** (connection refused, e.g. Redis not running) —
  should still report `"unhealthy"` and `503`, same as intended current fallback
  behavior, just now for the *correct* reason instead of always failing on a config
  bug.
- **Malformed `redis_url`** (e.g. missing scheme, or someone sets `REDIS_URL=""` in
  `.env`) — `from_url` may raise a different exception type than a connection error;
  confirm it's still caught by the surrounding `except Exception` rather than bubbling
  up as an unhandled 500.
