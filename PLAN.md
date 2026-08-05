## Solution plan

**Issue:** [Health check references settings.redis_host, which does not exist on Settings No. 155 - https://github.com/ascherj/pathreview/issues/155]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

Root cause: api/routes/health.py attempts to access settings.redis_host to inspect Redis health, but the Settings model in core/config.py does not define redis_host.

Expected behavior: The /health endpoint reads a valid redis_host setting, executes the Redis health probe, and returns the status properly.

Actual behavior: Accessing settings.redis_host raises an AttributeError, causing the request to crash before checking Redis.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

core/config.py: Add the redis_host field (and any default/type hints) to the Settings model.

api/routes/health.py: Verify that the route correctly reference settings.redis_host once the schema update is complete.

tests/ (or relevant route test files): Update or add a unit test for the /health endpoint to ensure it doesn't regression-crash.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

Define the redis_host field in the Settings class inside core/config.py with an appropriate default value (e.g., "localhost" or None) and type annotation (str or Optional[str]).

Verify environment variable loading so REDIS_HOST can be properly overridden at runtime if needed.

Check api/routes/health.py to ensure it gracefully handles missing/none or unconnectable Redis hosts.

Run or write unit tests covering GET /health to confirm the route returns expected health statuses without raising AttributeError.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Inputs: Environment variables (e.g., REDIS_HOST) or default configuration settings, along with GET requests to /health.

Outputs: A valid Settings object containing redis_host, enabling /health to output a structured HTTP JSON response reporting Redis status instead of throwing a 500 error.

### Risks & unknowns
What could go wrong? What are you still unsure about?

Type/Validation errors: If redis_host is mandatory without a default value, application startup will fail if REDIS_HOST is not set in the environment.

Connection handling: Simply adding redis_host will fix the AttributeError, but if Redis is actually down or unreachable, the probe might hang or throw a connection error if not wrapped in proper exception handling.

### Edge cases
What inputs or states should your fix handle gracefully?

Unset/Missing environment variable: redis_host should fallback gracefully to a default value (like "localhost") or handle None without crashing.

Unreachable Redis instance: The health check in health.py should catch connection timeouts or socket errors and return an "unhealthy" or "down" status response rather than letting an unhandled exception bubble up.