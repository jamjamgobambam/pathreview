# Solution Plan

## Issue
[Health check references settings.redis_host, which does not exist on Settings #155](https://github.com/ascherj/pathreview/issues/155)

### Understand
* **Root Cause:** `api/routes/health.py` attempts to connect to Redis by reading `settings.redis_host` and `settings.redis_port`. However, `Settings` in `core/config.py` only defines `redis_url`. This causes an `AttributeError` during the health probe.
* **Expected vs Actual:** Expected behavior is `/health` connecting to Redis using `redis.from_url(settings.redis_url)`. Actual behavior is catching an `AttributeError` and flagging Redis as `unhealthy`.

### Map
* **Files involved:**
  * `api/routes/health.py`
  * `core/config.py`
  * `tests/api/test_health.py` (or new test file)

### Plan
1. Refactor the Redis probe in `api/routes/health.py` to use `redis.from_url(settings.redis_url)`.
2. Ensure async execution or proper connection pooling for the health probe.
3. Write/update unit tests for `GET /health` asserting a `200 OK` response with `"redis": "healthy"` when Redis is reachable.
4. Verify using `make check` and `make test-unit`.

### Inputs & outputs
* **Input:** HTTP GET request to `/health`.
* **Output:** HTTP 200 JSON payload with `"redis": "healthy"`.

### Risks & unknowns
* Unhandled connection timeouts if Redis is down locally.

### Edge cases
* Malformed or missing `settings.redis_url`.
* Redis service temporarily unreachable.