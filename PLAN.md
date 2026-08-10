# Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

### Understand

**Root cause.** The Redis probe in `api/routes/health.py` builds its client from
`settings.redis_host` and `settings.redis_port`, but the `Settings` class in
`core/config.py` never defines those fields — it only defines `redis_url`.
Accessing `settings.redis_host` therefore raises
`AttributeError: 'Settings' object has no attribute 'redis_host'`.

**Expected vs. actual.**
- *Expected:* `GET /health` reports `dependencies.redis == "healthy"` when Redis is
  reachable, and only reports it `"unhealthy"` (and returns HTTP 503) when Redis is
  genuinely down.
- *Actual:* The `AttributeError` is swallowed by the probe's `try/except`, so Redis
  is **always** reported `"unhealthy"` and `/health` **always** returns HTTP 503 —
  even though the Redis container is running and healthy. Confirmed via the server
  log (`redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`)
  and a direct check (`hasattr(settings, 'redis_host')` is `False`).

### Map

Files involved:
- **`api/routes/health.py`** — the Redis probe (~lines 44–49) references
  `settings.redis_host` / `settings.redis_port`. This is where the fix lives.
- **`core/config.py`** — the `Settings` model; defines `redis_url` (line 12) but not
  `redis_host` / `redis_port`. Relevant if the chosen fix adds explicit fields.
- **`tests/integration/test_health_check.py`** — new reproduction test asserting
  Redis is reported healthy when the container is up (currently failing).

### Plan

1. **Fix the Redis probe** in `api/routes/health.py` to build the client from the
   setting that actually exists: `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
   Remove the references to `settings.redis_host` / `settings.redis_port`. (Preferred
   over adding new settings fields because it reuses existing config and is a single-file
   change; will confirm the maintainer's preference on the issue.)
2. **Keep the existing behaviour** of the probe: still `ping()` and set
   `dependencies.redis` to `"healthy"` / `"unhealthy"` and flip overall status on failure.
3. **Make the reproduction test pass** (`tests/integration/test_health_check.py`).
4. **Add a negative test** that points `redis_url` at an unreachable port (via
   monkeypatch) and asserts Redis is reported `"unhealthy"` and the endpoint returns
   503 — proving the fix reports *true* status rather than always-healthy.
5. **Run quality gates:** `ruff`, `black`, `mypy`, and the unit + integration tests
   before opening the PR.

### Inputs & outputs

- **Input:** `settings.redis_url` (e.g. `redis://localhost:6379/0`) and a running
  Redis instance.
- **Output / change:** `GET /health` returns `dependencies.redis == "healthy"` and,
  when all dependencies are healthy, HTTP 200; when Redis is unreachable it returns
  `"unhealthy"` + HTTP 503. No change to the response schema or to any public API
  contract — only the internal probe wiring changes.

### Risks & unknowns

- **Approach not yet confirmed with maintainer.** Two valid fixes exist (parse
  `redis_url` via `from_url`, or add `redis_host`/`redis_port` to `Settings`). I've
  asked on the issue; if they prefer explicit fields, the fix shifts to `core/config.py`.
- **Separate DB-probe bug (#154).** Even after this fix, an end-to-end `GET /health`
  may still return 503 because the Postgres probe (`await db.execute("SELECT 1")`)
  fails under SQLAlchemy 2.x. My reproduction test stubs the DB to isolate Redis, so
  this fix is verifiable independently, but I should note the interaction in the PR.
- **`redis_url` variants.** `from_url` must correctly handle a non-default DB index,
  credentials, or a `rediss://` (TLS) scheme. `redis.Redis.from_url` supports these,
  but I'll sanity-check with the local URL.
- **Blocking client in async endpoint.** The `redis` client is synchronous inside an
  `async` route (pre-existing); out of scope for this issue.

### Edge cases

- **Redis down / wrong port:** report `"unhealthy"` and 503 — do not raise/crash.
- **`redis_url` with a non-zero DB index or credentials:** connection still succeeds.
- **`rediss://` (TLS) URL:** parsed correctly by `from_url`.
- **Empty / malformed `redis_url`:** probe fails gracefully as `"unhealthy"` rather
  than raising an unhandled error.
