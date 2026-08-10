## Solution plan

**Issue:** Health check references settings.redis_host, which does not exist on Settings — https://github.com/ascherj/pathreview/issues/155

### Understand
The `/health` endpoint's Redis check calls `settings.redis_host` and
`settings.redis_port` to build a `redis.Redis(...)` connection. Neither
attribute exists on the `Settings` class — the config only defines a single
combined `REDIS_URL` (e.g. `redis://localhost:6379/0`). Every call to this
code path raises an `AttributeError`, which is caught by a broad
`except Exception` block and silently reported as `"redis": "unhealthy"`.
Expected behavior: the health check should connect to Redis using the
actual `redis_url` config value and report `"healthy"` when Redis is
genuinely reachable. Actual behavior: it always reports `"unhealthy"`
regardless of Redis's real status, making the health check useless for its
intended purpose (and would return a false 503 in production monitoring).

### Map
- `api/routes/health.py` — contains the buggy Redis check block (references
  `settings.redis_host` / `settings.redis_port`); this is the primary file
  to change.
- `core/config.py` — where the `Settings` class is defined; need to confirm
  the exact attribute name (`redis_url`) and type available here.
- `.env` / `.env.example` — confirms only `REDIS_URL` is defined, no split
  host/port variables.
- `tests/` (whichever test file covers `api/routes/health.py`, if one
  exists) — will need a new or updated test for the fixed behavior.

### Plan
1. Inspect `core/config.py` to confirm the exact `Settings` attribute name
   and type for the Redis connection string (`redis_url`).
2. Update `api/routes/health.py` to build the Redis client from
   `settings.redis_url` instead of the non-existent `redis_host`/`redis_port`
   fields — likely via `redis.Redis.from_url(settings.redis_url, ...)`
   rather than manually passing `host=`/`port=`.
3. Manually re-test locally: run `curl http://127.0.0.1:8000/health` with
   Redis running (expect `"redis": "healthy"`) and with Redis stopped via
   `docker compose stop redis` (expect `"redis": "unhealthy"`, proving the
   check is now accurate in both directions).
4. Add/update an automated test for the health endpoint's Redis check,
   covering both the healthy and unhealthy cases.
5. Clean up: remove the now-unnecessary `import redis` duplication if any,
   confirm logging messages (`redis_health_check_passed` /
   `_failed`) still fire correctly.

### Inputs & outputs
**Input:** the `Settings` object's Redis connection string (`redis_url`),
and the real-time state of the Redis service it points to.
**Output:** an accurate `"redis": "healthy"` or `"redis": "unhealthy"` value
in the `/health` endpoint's JSON response, matching Redis's actual
reachability rather than always failing due to the config bug.

### Risks & unknowns
- Unsure whether `redis.Redis.from_url()` behaves identically to the
  current `redis.Redis(host=..., port=...)` call in terms of timeouts /
  `decode_responses` — need to check the `redis` library docs for
  equivalent kwargs.
- Unclear whether other parts of the codebase (outside `health.py`) also
  reference `settings.redis_host`/`redis_port` and would need the same fix
  — a repo-wide search for those attribute names is needed before
  considering this fully resolved.
- Risk of masking a *different* real Redis outage during testing if Docker
  containers are flaky (as I saw firsthand this week) — need to verify
  Docker state independently (`docker compose ps`) before trusting any
  single test run.

### Edge cases
- Redis genuinely down/unreachable (container stopped) → should report
  `"unhealthy"` with a clear log message, not crash the whole endpoint.
- Malformed or missing `REDIS_URL` in `.env` → should fail gracefully with
  a logged error, not an unhandled exception that takes down the health
  endpoint.
- Redis reachable but slow to respond → should ideally still resolve within
  a reasonable timeout rather than hanging the health check indefinitely
  (worth checking if `redis.Redis.from_url` needs an explicit
  `socket_timeout` set).
