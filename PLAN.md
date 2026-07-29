# Solution plan

**Issue:** [#155 — Health check references `settings.redis_host`, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

### Understand

**Root cause.** The Redis probe in `api/routes/health.py` constructs its client from
`settings.redis_host` and `settings.redis_port`:

```python
r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True,
)
```

But `Settings` in `core/config.py` never declares those fields — it defines a single
`redis_url` (`redis://localhost:6379/0`). Because Pydantic settings don't expose
attributes that weren't declared, `settings.redis_host` raises
`AttributeError: 'Settings' object has no attribute 'redis_host'`.

**Expected vs. actual.**
- *Expected:* `GET /health` builds a Redis client, pings it, and reports
  `redis: "healthy"` (HTTP 200) when Redis is reachable.
- *Actual:* the attribute access raises `AttributeError` inside the Redis `try` block.
  The handler's `except Exception` catches it, logs `redis_health_check_failed`, and sets
  `redis: "unhealthy"` + overall `status: "unhealthy"`, so the endpoint returns **HTTP 503
  even when Redis is up**. Reproduced locally — see `tests/unit/test_health.py` and the
  Week 8 JOURNAL entry (captured log line:
  `redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`).

`redis_host`/`redis_port` appear in exactly one place in the codebase (this handler);
every other Redis consumer receives an already-built client. So `redis_url` is the
established single source of truth, and the handler is the outlier.

### Map

Files / functions I expect to touch:

- **`api/routes/health.py`** → `health_check()`, the Redis `try` block (lines ~44-49).
  This is the actual fix.
- **`tests/unit/test_health.py`** → update the reproduction test so the currently-failing
  `test_health_reports_redis_healthy_when_reachable` asserts the fixed behavior and passes;
  keep/adjust `test_settings_is_missing_redis_host_and_port` (it documents the pre-fix state
  and will be repurposed or removed once the fix lands).

Files I expect to read but **not** change (unless investigation says otherwise):

- **`core/config.py`** → `Settings`. Confirms `redis_url` exists and `redis_host`/
  `redis_port` do not. Only touched if I decide to derive/add fields here instead.
- **`.env.example`** / **`docker-compose.yml`** → confirm `REDIS_URL` is the configured
  variable, so the fix doesn't require new env vars.

### Plan

1. **Reproduce (done in Week 8).** Failing test `test_health_reports_redis_healthy_when_reachable`
   proves `GET /health` returns 503 because of the missing setting.
2. **Apply the fix in `health.py`.** Replace the host/port constructor with a single
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)`. `from_url` parses the
   host, port, and `/0` database index out of the existing URL, so no config change is
   needed and Redis stays a single source of truth.
3. **Turn the reproduction test green.** Re-run `tests/unit/test_health.py` and confirm
   `test_health_reports_redis_healthy_when_reachable` now passes; update the
   root-cause test so the suite reflects the fixed state (no lingering assertion that the
   attribute is missing).
4. **Add a negative-path test.** Assert that when `.ping()` raises (Redis down), the
   endpoint reports `redis: "unhealthy"` and returns HTTP 503 — guarding the error handling
   we're relying on.
5. **Run the full local gate.** `make check` (ruff + black + mypy) and `make test-unit`,
   then open the PR against `ascherj/pathreview` using the PR template.

### Inputs & outputs

- **Input to the fix:** `settings.redis_url` — a connection string, e.g.
  `redis://localhost:6379/0`, already loaded from the `REDIS_URL` env var / `.env`.
- **Output / behavior change:** `health_check()` returns a JSON body whose
  `dependencies.redis` is `"healthy"` (HTTP 200) when Redis responds to `ping()`, and
  `"unhealthy"` (HTTP 503) when it doesn't — instead of unconditionally 503.
- **Signature changes:** none. `health_check()` keeps its route (`GET /health`), parameters,
  and response shape. The only change is *how* the Redis client is constructed. No public
  API, config schema, or env var changes.

### Risks & unknowns

- **`redis.Redis.from_url` argument compatibility** (`api/routes/health.py`): need to confirm
  `from_url` accepts `decode_responses=True` as a keyword on `redis>=5.0.0` (the pinned
  version) and that it parses the `/0` db segment as the current `db=0` did. Mitigation: a
  quick check against the installed `redis` version plus the passing test.
- **Alternative approach not taken** (`core/config.py`): adding explicit `redis_host`/
  `redis_port` fields would also silence the error but creates two overlapping ways to
  configure Redis that can silently diverge from `redis_url`. I'm choosing the `from_url`
  approach; the risk of the alternative is documented here so reviewers see it was
  considered.
- **Test import weight** (`tests/unit/test_health.py`): importing `api.routes.health` pulls
  in `core.database`, which builds a SQLAlchemy async engine at import time. The reproduction
  test already handles this by overriding `get_db` and stubbing Redis, but I need to keep the
  test free of any real network/DB connection so it stays a true unit test.
- **Unknown:** whether other endpoints/scripts read `redis_url` in a way that assumes a
  specific format — grep confirms only this handler touches Redis config directly, but I'll
  re-verify before the PR.

### Edge cases

- **Redis unreachable / connection refused:** `.ping()` raises → endpoint must report
  `redis: "unhealthy"` and return HTTP 503 (not crash).
- **Malformed or empty `redis_url`:** `from_url` may raise on an invalid string → the
  existing `try/except` must still catch it and report `unhealthy` rather than surfacing a
  500.
- **Non-default database index in the URL** (e.g. `redis://host:6379/2`): the client must
  honor the db segment from the URL rather than forcing `db=0`.
- **URL with credentials / TLS scheme** (e.g. `rediss://user:pass@host:6380/0`): building via
  `from_url` should preserve auth and scheme, whereas the old host/port constructor silently
  dropped them — worth an assertion or at least a documented expectation.
- **All dependencies healthy:** overall `status` is `"healthy"` and the endpoint returns
  HTTP 200 with `redis: "healthy"` — the primary case the reproduction test locks in.
