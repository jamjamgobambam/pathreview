## Solution plan

**Issue:** Health check references settings.redis_host, which does not exist on Settings ([Issue #155](https://github.com/ascherj/pathreview/issues/155))

### Understand
The root cause is a configuration contract mismatch between the health endpoint and the settings model.

Expected behavior:
- The health endpoint should construct a Redis client from `settings.redis_url`.
- If Redis is reachable, Redis dependency health should be `healthy`.

Actual behavior in the buggy version:
- The health endpoint attempted to read `settings.redis_host` and `settings.redis_port`, which are not defined in `core/config.py`.
- This caused the Redis probe path to fail, marking service health as `unhealthy` and returning HTTP 503 even when Redis configuration existed via `redis_url`.

### Map
Primary files/functions/modules involved:
- `api/routes/health.py`
  - `health_check` route function
  - Redis probe and PostgreSQL probe logic
- `core/config.py`
  - `Settings` fields that define Redis configuration surface
- `tests/unit/test_health_route.py`
  - Unit tests that validate healthy and unhealthy dependency outcomes

Files expected to be touched:
- `api/routes/health.py`
- `tests/unit/test_health_route.py`
- `JOURNAL.md` (reproduction record)
- `PLAN.md` (this plan)

### Plan
1. Reproduce the mismatch locally.
   - Confirm the old route logic expects `redis_host`/`redis_port`.
   - Confirm `Settings` only exposes `redis_url`.
2. Update health route Redis initialization.
   - Use `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
   - Keep status semantics unchanged (`healthy` vs `unhealthy`).
3. Add/confirm regression-focused unit tests.
   - Healthy path: dependencies all pass -> HTTP 200 response payload from route function.
   - Redis failure path: probe failure -> HTTP 503 with `redis` dependency marked `unhealthy`.
4. Validate behavior with targeted tests.
   - Run `pytest tests/unit/test_health_route.py -v -m unit`.
5. Document reproduction and solution plan.
   - Add Week 8 journal entry with commit links and open questions.

### Inputs & outputs
Inputs:
- Runtime settings from `core.config.settings` (especially `redis_url` and `vector_db_url`).
- Dependency probe outcomes:
  - PostgreSQL query result
  - Redis `ping()` result

Outputs:
- Health response payload with:
  - top-level `status`
  - dependency statuses for `postgres`, `redis`, `vector_db`
  - timestamp and safety event counter
- HTTP status behavior:
  - `200` when dependencies are healthy/available
  - `503` when a critical dependency probe fails

### Risks & unknowns
- Risk: Test patching can miss the import location used inside `health_check`.
  - Investigation path: verify patch target in `tests/unit/test_health_route.py` matches runtime import behavior in `api/routes/health.py`.
- Risk: SQLAlchemy execution API differences can cause DB probe regressions.
  - Investigation path: keep query wrapped in `text("SELECT 1")` and validate with unit/integration checks.
- Risk: Existing baseline repo failures can hide issue-specific validation signal.
  - Investigation path: run targeted test file first, then report unrelated failures separately.

### Edge cases
- Redis URL present but Redis service unreachable: return HTTP 503 and mark only Redis unhealthy.
- Redis URL malformed: handle exception path gracefully and return unhealthy status.
- Database probe failure with Redis healthy: still return HTTP 503 due to critical dependency failure.
- `vector_db_url` missing/empty: mark vector DB as unavailable without crashing.
- Multiple dependency failures in same request: preserve per-dependency status and overall unhealthy result.
