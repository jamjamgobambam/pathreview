# Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings
https://github.com/ascherj/pathreview/issues/155

## Understand

The health check creates a Redis client using `settings.redis_host` and `settings.redis_port`. These configuration fields do not exist in `core/config.py`, causing an `AttributeError` whenever the Redis health check runs. The expected behavior is to use the existing `settings.redis_url` configuration.

## Map

Files involved:

- api/routes/health.py
- core/config.py

## Plan

1. Reproduce the AttributeError by calling the `/health` endpoint.
2. Verify that Redis is configured through `settings.redis_url`.
3. Replace the `redis.Redis(...)` constructor with `redis.from_url(settings.redis_url)`.
4. Verify that the `/health` endpoint returns a health response instead of crashing.

## Inputs & outputs

**Input**

- Existing Redis URL from `settings.redis_url`

**Output**

- Health endpoint successfully creates a Redis client using the configured Redis URL.

## Risks & unknowns

- Existing health check failures may still occur if Redis or PostgreSQL are unavailable.
- Pre-existing lint/type-check issues in `api/routes/health.py` may affect development but are unrelated to this fix.

## Edge cases

- Invalid Redis URL
- Redis server unavailable
- Other dependency health checks failing while Redis client creation succeeds