## Solution plan

**Issue:** Health check references settings.redis_host, which does not exist on Settings (#155)

### Understand
* **Root cause:** The health check endpoint at `api/routes/health.py` expects `settings.redis_host` to exist in order to test the Redis connection. However, `redis_host` is missing from the `Settings` class in `core/config.py`.
* **Actual behavior:** Hitting `GET /health` logs a Python `AttributeError: 'Settings' object has no attribute 'redis_host'` and returns a 503 status with Redis marked as "unhealthy".
* **Expected behavior:** `Settings` defines `redis_host` so the health check can properly attempt the connection without throwing an attribute error.

### Map
* `core/config.py`: I will add the `redis_host` variable to the `Settings` class.

### Plan
1. Reproduce the error by calling `GET /health` locally (Completed).
2. Open `core/config.py`.
3. Locate the `Settings` class and add `redis_host: str = "localhost"` (or check how other host variables are defined and match the pattern).
4. Restart the server and re-run `curl http://localhost:8000/health`.
5. Verify the `AttributeError` for Redis no longer appears in the terminal logs.

### Inputs & outputs
* **Input:** Environment variables / Settings model configuration.
* **Output:** `settings.redis_host` resolves to a string, allowing the Redis health check logic to execute properly.

### Risks & unknowns
* Low risk. I need to observe how `core/config.py` handles defaults (e.g., if it uses `pydantic` fields or standard strings) to match the existing code style.
* **Out of scope observation:** During reproduction, I noticed a separate Postgres error in the logs: `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`. I am documenting it here for visibility, but it is outside the scope of this Redis-specific fix.

### Edge cases
1. **Redis server offline:** If Redis isn't running locally, the health check might still say "unhealthy" (due to a connection refusal), but it must gracefully handle the failure and *not* crash with an `AttributeError`.
2. **Environment variable override:** If a user explicitly sets `REDIS_HOST` in their `.env` file or Docker environment (e.g., `REDIS_HOST="redis-server"`), the Pydantic `Settings` model must prioritize that value over the default `"localhost"`.