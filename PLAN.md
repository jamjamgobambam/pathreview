# Solution plan

**Issue:** [Health check references settings.redis_host, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

## Understand

**What is the root cause?**
The health check endpoint at `api/routes/health.py` tries to access `settings.redis_host` and `settings.redis_port`, but these fields don't exist in the Settings model defined in `core/config.py`. The Settings model only defines `redis_url`. The error is caught by an exception handler and always reports Redis as "unhealthy" even when it's actually running.

**Reproduction evidence:**

***What I did***
# 1. Started the app
make run

# 2. In a new terminal, tested the health endpoint
curl http://localhost:8000/health

***What I saw***
``` JSON

{
  "detail": {
    "status": "unhealthy",
    "dependencies": {
      "postgres": "unhealthy",
      "redis": "unhealthy",  // ❌ BUG: Redis is actually running!
      "vector_db": "healthy"
    }
  }
}

```

### How I Verified Redis is Actually Running:

- Check Redis container status
docker compose ps
 Output: pathreview-redis-1   Up 6 days (healthy)

- Test Redis directly
docker exec -it pathreview-redis-1 redis-cli ping
  Output: PONG ✅

### Conclusion:
✅ BUG CONFIRMED: Redis is running and responding, but the health check says it's unhealthy!

## Map

**Files I'll touch:**
1. `api/routes/health.py` - Lines 37-44 (the Redis connection code)
2. `tests/unit/test_health.py` - Already created, may need updates

**Functions involved:**
- `health_check()` in `api/routes/health.py`
- `Settings` class in `core/config.py` (has `redis_url`)

## Plan

### Sub-task 1: Update Redis connection in health check
- Replace lines 39-40: `redis.Redis(host=settings.redis_host, port=settings.redis_port)`
- With: `redis.Redis.from_url(settings.redis_url)`

### Sub-task 2: Test the fix locally
- Run `make run`
- Call `curl http://localhost:8000/health`
- Verify `"redis": "healthy"` appears

### Sub-task 3: Run tests
- Run `make check` (lint, format, type check)
- Run `make test-unit` to ensure all tests pass

### Sub-task 4: Update tests if needed
- If the health tests need adjustment, update them
- Ensure both healthy and unhealthy scenarios are covered

### Sub-task 5: Open PR
- Follow PR template
- Include before/after screenshots or curl outputs
- Reference issue #155

## Inputs & outputs

**Inputs:**
- `settings.redis_url` from `.env` (e.g., `redis://localhost:6379/0`)
- Redis server availability (running or down)

**Outputs:**
- ✅ `"redis": "healthy"` when Redis is running
- ❌ `"redis": "unhealthy"` when Redis is down
- Correct HTTP status (200 OK or 503 Service Unavailable)

## Risks & unknowns

**What could go wrong?**

1. **Redis URL format**: The URL might be malformed or missing
   - Mitigation: The URL comes from Settings with a valid default
   - Add try/except to handle connection errors gracefully

2. **Tests might need adjustment**: The health tests use mocks
   - Mitigation: The tests already work, just need to verify they pass after the fix

3. **Other students working on same issue**: Multiple PRs for same issue
   - Mitigation: The course allows multiple PRs; grade is based on my work

4. **PostgreSQL showing unhealthy**: This is a separate issue
   - Mitigation: My fix only addresses Redis, won't affect PostgreSQL

## Edge cases

**What should the fix handle gracefully?**

1. **Redis is down** → Should report "unhealthy"
2. **Redis is running** → Should report "healthy"
3. **Redis URL is invalid** → Should report "unhealthy" with error log
4. **Redis connection timeout** → Should report "unhealthy"
5. **PostgreSQL check** → Should continue to work independently

## Testing Plan

| Scenario | Expected Result |
|----------|-----------------|
| Redis running | `"redis": "healthy"` |
| Redis stopped | `"redis": "unhealthy"` |
| Redis restarted | `"redis": "healthy"` |