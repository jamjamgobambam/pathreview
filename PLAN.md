## Solution plan

**Issue:** [Health check references settings.redis_host, which does not exist on Settings. https://github.com/ascherj/pathreview/issues/155]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The core issue for this bug is that the `redis_host` field is missing from `Settings` in config.py, which raises an AttributeError when it's referenced within api/routes/health.py. When Redis is reachable, GET /health should report "redis": "healthy" in the response, with an overall 200 OK status. Right now, even when Redis is actually reachable, the health check crashes with an AttributeError ('Settings' object has no attribute 'redis_host'), which gets silently caught by the broad except Exception block causing the endpoint to falsely report "redis": "unhealthy" and return an overall 503 Service Unavailable, regardless of Redis's real status.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

### Map

- `api/routes/health.py` — contains the actual bug (the Redis probe) and is where my fix lives (replacing the broken `host=`/`port=` call with `redis.Redis.from_url()`).
- `core/config.py` — read closely to understand the `Settings` class and `redis_url` field; not modified in the final fix, but important context since it's the single source of truth for Redis connection info.
- `tests/unit/test_health.py` (new file) — doesn't exist yet; I'll create it to add the first test coverage for the `/health` endpoint, following the naming pattern used by other files in `tests/unit/`.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

Step 1: Replace the broken redis.Redis(host=settings.redis_host, port=settings.redis_port, ...) call in health.py with redis.Redis.from_url(settings.redis_url, decode_responses=True), avoiding the need for separate host/port fields on Settings

Step 2: Create tests/unit/test_health.py (doesn't exist yet) with at least two test cases: one confirming /health reports "redis": "healthy" when Redis is reachable, and one confirming it reports "redis": "unhealthy" (not a raised exception) when Redis is unreachable since the endpoint should degrade gracefully, not crash.

Step 3: Run mypy on health.py and config.py before and after the fix to confirm the fix resolves the redis_host/redis_port attribute errors without introducing new ones (confirmed: errors dropped from 11 to 8, with the remaining 8 being pre-existing and unrelated to this issue).

Step 4: Write up the PR description documenting the fix, including the additional redis_port bug discovered beyond the original issue text, and the reasoning for choosing from_url() over adding new Settings fields.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

"The input is settings.redis_url, which comes from the .env file (or environment variables, with a hardcoded default as fallback), and represents a full Redis connection string containing the host, port, and database number.

The fix produces an accurate reflection of Redis's real status: \"redis\": \"healthy\" with an overall 200 OK when Redis is reachable, and \"redis\": \"unhealthy\" with a 503 Service Unavailable when it's genuinely down  rather than always reporting unhealthy regardless of Redis's actual state.

### Risks & unknowns
What could go wrong? What are you still unsure about?

There are pre-existing issues in health.py outside this fix's scope — the 8 remaining mypy errors (missing type annotations, indexed-assignment issues) and the separate Postgres health check bug ('SELECT 1' should be explicitly declared as text('SELECT 1'))that could make the health endpoint's overall reliability look worse than it is, even though they're unrelated to the Redis fix.


I'm not fully certain how redis.Redis.from_url() behaves if settings.redis_url is malformed or empty (e.g., missing the redis:// scheme) whether it fails immediately with a clear error, or fails in some way that doesn't get caught cleanly by the existing except Exception block.





### Edge cases
What inputs or states should your fix handle gracefully?


When Redis is down but redis_url is valid, the fix should gracefully report \"redis\": \"unhealthy\" rather than crashing the whole app I confirmed this behavior when Docker wasn't running and /health returned \"redis\": \"unhealthy\" with an overall 503, without any unhandled exception.


"If redis_url is empty or malformed, the fix should still gracefully report \"redis\": \"unhealthy\" (caught by the existing except Exception block and logged via log.error(...)) rather than causing an unhandled crash that takes down the entire /health endpoint.