## Solution plan

**Issue:** Health check references settings.redis_host, which does not exist on Settings
https://github.com/ascherj/pathreview/issues/155

### Understand
The health check endpoint tries to check Redis by reading settings.redis_host
and settings.redis_port. Neither field exists on the Settings model, only
redis_url does. Because of this, the Redis check always fails with an
AttributeError, caught inside a try/except block, so the app does not
crash, but /health always reports Redis as unhealthy, even when Redis is
running fine. The expected behavior is for the health check to correctly
connect to Redis using the settings that actually exist, and report the
real status.

### Map
Files expected to touch:
- api/routes/health.py, the redis check block, around lines 30 to 40. This
  needs to build the Redis client from redis_url instead of the missing
  redis_host and redis_port fields.
- core/config.py, to confirm redis_url is the correct field to use, and to
  check if it needs a default value change.
- tests/unit/test_health.py, the reproduction test added this week. This
  test will need to be updated once the fix is in place, so it checks for
  the correct passing behavior instead of the current failing behavior.

### Plan
1. Read how redis_url is used elsewhere in the codebase, if anywhere, to
   confirm the expected connection pattern.
2. Update api/routes/health.py to build the Redis client using
   redis.Redis.from_url(settings.redis_url) instead of the missing host
   and port fields.
3. Run the app locally and confirm GET /health now reports redis as
   healthy, when Redis is running.
4. Update tests/unit/test_health.py to reflect the fixed behavior, add a
   test for the healthy case, and keep or adjust the unhealthy case if
   still relevant, for example when Redis is down.
5. Run make check and make test-unit to confirm the fix passes all
   project checks.

### Inputs & outputs
Input: the redis_url string from Settings, for example
redis://localhost:6379/0.
Output: the health_status dictionary, specifically
dependencies.redis being set to healthy or unhealthy correctly, based on
whether Redis actually responds to a ping.

### Risks & unknowns
- Not fully sure yet if redis.Redis.from_url is the correct method for
  this codebase's version of the redis package, this needs checking.
- The mypy errors already present in health.py, unrelated to this bug,
  may need to be addressed too, since they block clean commits.
- Need to confirm this fix does not affect the vector_db check or
  postgres check, which live in the same function.

### Edge cases
- Redis being down or unreachable, should still report unhealthy, not
  crash.
- redis_url being malformed or missing, should fail gracefully with a
  clear error, not crash the whole health check.
- Redis running but slow to respond, should ideally still return quickly,
  though this may be out of scope for this fix.