## Solution plan

**Issue:** Health check references settings.redis_host, which does not exist on Settings — https://github.com/ascherj/pathreview/issues/155

### Understand
The root cause is confirmed: `api/routes/health.py` builds a `redis.Redis()` client using `settings.redis_host` and `settings.redis_port`, but `core/config.py`'s `Settings` model only defines `redis_url` (a full connection string like `redis://localhost:6379/0`) — it never defines separate host/port fields. Expected behavior: the health check connects to Redis using existing config and accurately reports its real status. Actual behavior (confirmed via local reproduction): every call to `GET /health` raises `AttributeError: 'Settings' object has no attribute 'redis_host'`, which is caught by the endpoint's `try/except` and silently reported as `"redis": "unhealthy"` — even when Redis itself is running and healthy, as confirmed by `docker compose ps`.

### Map
- `api/routes/health.py` — the `health_check` function, specifically the Redis check block (`r = redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`).
- `core/config.py` — the `Settings` model, which defines `redis_url` but not `redis_host`/`redis_port`.
- Test file for this route — still need to locate (likely `tests/unit/test_health.py` or similar); not yet confirmed. This is an open item for early Week 9.

### Plan
1. Grep the whole repo (not just `health.py`) for any other references to `settings.redis_host` or `settings.redis_port`, to make sure I catch every place this bug shows up, not just the one in the issue.
2. Locate and read the existing test file for `/health` to understand the mocking conventions used for Postgres/Redis/vector_db checks before writing new tests.
3. Replace the `redis.Redis(host=..., port=...)` construction with `redis.from_url(settings.redis_url)`, which parses the existing connection string directly instead of relying on fields that don't exist.
4. Manually re-verify locally: hit `/health` with Redis running (expect `"redis": "healthy"`), then stop the Redis container and hit `/health` again (expect a genuine `"unhealthy"`, not an AttributeError) — confirming the fix distinguishes real failures from config bugs.
5. Write or update a unit test that mocks `redis.from_url` to cover both the healthy and unhealthy paths.

### Inputs & outputs
Input: the existing `settings.redis_url` config value. Output: an accurate `"redis"` status field in the `/health` JSON response — `"healthy"` when Redis is genuinely reachable, `"unhealthy"` when it genuinely isn't (not due to a missing config attribute).

### Risks & unknowns
- `redis.from_url()` may not support every option the old `host`/`port` approach implicitly assumed (e.g. TLS, auth) — need to check the `redis-py` docs before finalizing.
- Haven't yet located the test file for `/health` — if none exists, I'll need to create one from scratch rather than extend an existing pattern, which adds scope.
- The unrelated Postgres failure I saw during reproduction (`Textual SQL expression should be explicitly declared as text('SELECT 1')`) is a separate SQLAlchemy 2.x issue in the same function — I need to make sure my diff doesn't accidentally touch that code path while editing nearby lines.

### Edge cases
- `redis_url` is empty or malformed — `from_url()` should raise a clear, catchable exception, not crash the whole endpoint.
- Redis is reachable but slow/times out — should report `"unhealthy"` rather than hang the health check indefinitely.
- `redis_url` includes an embedded password (e.g. `redis://:password@host:port/0`) — confirm `from_url()` correctly parses credentials rather than silently dropping them.