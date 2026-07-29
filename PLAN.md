## Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings (#155)](https://github.com/ascherj/pathreview/issues/155)

### Understand

The Redis probe inside `health_check()` (in `api/routes/health.py`, lines 39-56) builds a
`redis.Redis` client using `host=settings.redis_host` and `port=settings.redis_port`.
Neither field exists on the `Settings` model in `core/config.py` — the only Redis-related
field defined there is `redis_url` (e.g. `redis://localhost:6379/0`). Accessing
`settings.redis_host` raises an `AttributeError`.

Because that whole block is wrapped in `except Exception as exc`, the error doesn't crash
the request — it's silently caught, logged, and used to mark `dependencies.redis` as
`"unhealthy"`, which in turn sets the overall `status` to `"unhealthy"` and makes the route
raise a 503. Net effect: **`GET /health` always reports Redis as down and returns 503,
even when Redis is running perfectly fine**, because the probe never actually reaches
`r.ping()`.

Expected behavior: the Redis probe should connect using the connection info that actually
exists (`redis_url`), correctly report `"healthy"` when Redis is reachable, and only report
`"unhealthy"` on a genuine connection failure.

### Map

Files/functions I expect to touch:

- `api/routes/health.py` — `health_check()`, specifically the Redis try/except block
  (lines 39-56). This is the only production code that needs to change.
- `core/config.py` — `Settings` class. Not expected to need changes (it already has
  `redis_url`), but I'll double check no other code path also assumes `redis_host`/`redis_port`
  exist before ruling that out.
- `tests/unit/test_health.py` — the reproduction test I wrote in Week 8. I'll update its
  assertions once the fix lands so it verifies the *correct* behavior (redis healthy)
  instead of just documenting the current bug.

### Plan

1. Search the codebase for any other references to `redis_host`/`redis_port` (`grep -rn "redis_host\|redis_port"`) to confirm `health.py` is the only call site — avoids fixing one spot and missing another.
2. In `api/routes/health.py`, replace the `redis.Redis(host=..., port=...)` construction with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`, which parses host/port/db directly from the existing connection string.
3. Manually verify against the running app: start `make run`, hit `curl localhost:8000/health`, and confirm the response now shows `"redis": "healthy"` and overall `"status": "healthy"` (assuming Postgres and vector DB are also up).
4. Update `tests/unit/test_health.py`: keep the existing root-cause test (`test_settings_has_no_redis_host_or_port_field` still documents that those fields don't exist and never should), but change the end-to-end test to assert the health check now returns 200 with `"redis": "healthy"`, and add a new test that mocks a real Redis connection failure to confirm `"unhealthy"` is still reported correctly when Redis is actually down.
5. Run `make check` (ruff, black, mypy) and `make test-unit` to confirm nothing else broke, then open the PR referencing `Fixes #155`.

### Inputs & outputs

- **Input:** the module-level `settings` singleton from `core/config.py` (specifically `settings.redis_url`, a string like `redis://localhost:6379/0`) and the live/mocked `db` dependency passed into `health_check()`.
- **Output:** the JSON health response dict, specifically `dependencies.redis` (`"healthy"` / `"unhealthy"`) and the top-level `status`/HTTP status code, which downstream depend on (e.g. Docker healthchecks or uptime monitors hitting `/health`).
- No function signatures change — `health_check(db=Depends(get_db))` stays the same; only the internal Redis-connection logic changes.

### Risks & unknowns

- **Risk:** `redis.Redis.from_url()` needs `decode_responses=True` passed explicitly (it's not part of the URL) — if I forget it, behavior changes subtly (bytes vs str responses) even though the health check itself doesn't care. Need to double check this doesn't affect anything downstream that imports this same client pattern.
- **Unknown:** I haven't confirmed whether any other part of the codebase (outside `api/routes/health.py`) constructs a Redis client using host/port instead of `redis_url` — need to grep for `redis.Redis(` usages across the repo before assuming this is the only fix needed.
- **Risk:** the existing reproduction test's second assertion (`detail["dependencies"]["redis"] == "unhealthy"`) will need to flip to `"healthy"` after the fix — if I forget to update it, CI will fail even though the fix is correct. Tracking this explicitly in sub-task 4 above.

### Edge cases

- **Redis actually down/unreachable:** the fix must still report `"unhealthy"` in this case (i.e., `from_url()` + `r.ping()` failing should still be caught and reported correctly) — not just always report healthy regardless of real Redis state.
- **Malformed `REDIS_URL` in `.env`** (e.g. missing scheme, typo'd host): `from_url()` should raise a connection/parsing error that gets caught by the existing `except Exception` block and reported as `"unhealthy"`, rather than crashing the whole endpoint with an unhandled exception.
- **Redis reachable but slow/timing out:** worth checking whether `redis.Redis.from_url()` needs an explicit `socket_connect_timeout` so a hung Redis doesn't hang the entire `/health` endpoint indefinitely.
