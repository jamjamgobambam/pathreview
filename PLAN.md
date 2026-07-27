## Solution plan

**Issue:** Health check references settings.redis_host, which does not exist on Settings — #155
https://github.com/ascherj/pathreview/issues/155

### Understand
The `/health` endpoint's Redis probe in `api/routes/health.py` references
`settings.redis_host`, but `Settings` (in `core/config.py`) has no such field. 
It does define `redis_url: str = Field(default="redis://localhost:6379/0")`.
But it is a naming mismatch as the health check was written against a field name that never existed, likely
a typo or leftover from an earlier version of the config. Expected behavior: `/health` should connect using `settings.redis_url` and report real Redis
connectivity status.

### Map
- `api/routes/health.py` — contains the Redis probe with the incorrect
  `settings.redis_host` needs to be updated to `settings.redis_url`
- `core/config.py` — `redis_url` already exists and
  is correctly defined

### Plan
1. Open `api/routes/health.py` and locate the exact line(s) referencing
   `settings.redis_host`
2. Confirm how the Redis client/connection is initialized elsewhere in the
   codebase (if any existing Redis client exists, check how it consumes
   `redis_url`, since it may need a client object rather than a raw string)
3. Update the reference from `settings.redis_host` to `settings.redis_url`
4. Run locally and hit `GET /health` to confirm no AttributeError and that
   Redis status now reflects actual connectivity
5. Add or update a test asserting `/health` doesn't crash and correctly
   reports Redis status using `redis_url`

### Inputs & outputs
**Input:** `GET /health` request
**Output:** JSON response with an accurate Redis health status (healthy if
reachable at `redis_url`, unhealthy if not) 

### Risks & unknowns
- Need to confirm whether the Redis probe expects just the URL string, or
  needs to construct a client (e.g. via `redis.asyncio.from_url()`)
- A local Redis instance needs to actually be running for the probe to
  return "healthy"; need to confirm this is set up in my dev environment
- A separate, unrelated postgres health check error also appears in the
  same endpoint (a SQLAlchemy textual SQL issue: raw `"SELECT 1"` needs to
  be wrapped in `text()`)

### Edge cases
- `redis_url` is reachable & should report "healthy"
- Redis server down/unreachable at that URL & should report "unhealthy"
  gracefully, not throw an unhandled exception
- Redis reachable but slow to respond & should still return within a
  reasonable time rather than hanging indefinitely