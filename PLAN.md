## Solution plan

**Issue:** Add safety event count to health check endpoint

**Issue link:** https://github.com/ascherj/pathreview/issues/68

### Understand

The `/health` endpoint currently reports the health of PostgreSQL, Redis, and the vector database, but it does not report the number of safety events recorded during the last hour.

The safety monitoring module already stores counts in Redis using keys such as `safety:events:<event_type>`. The missing behavior is connecting those existing counters to the health endpoint.

Expected behavior:
- The `/health` response includes a `safety_events_last_hour` field.
- The value represents the total count across all valid safety event types.
- If no safety events exist, the value is `0`.
- A failure to read the safety count should not crash the entire health endpoint.

Actual behavior before the fix:
- The endpoint either omitted the field or returned a hard-coded value of `0`.
- It did not query the safety monitoring counters stored in Redis.

### Map

Files and components involved:

- `api/routes/health.py`
  - Contains the `/health` endpoint.
  - Performs dependency checks.
  - Will retrieve and expose the safety-event count.

- `safety/monitoring.py`
  - Contains `SafetyMonitor`.
  - Defines `VALID_EVENT_TYPES`.
  - Provides `get_event_count()` for reading event counters from Redis.

- `JOURNAL.md`
  - Documents the reproduction steps and planning work.

- `PLAN.md`
  - Documents the intended implementation approach.

### Plan

1. Reproduce the missing behavior by starting the local services and requesting the `/health` endpoint.
2. Confirm that the response does not calculate the safety-event count from Redis and identify the placeholder or missing implementation in `api/routes/health.py`.
3. Reuse the Redis client created during the Redis health check and initialize `SafetyMonitor`.
4. Iterate over `SafetyMonitor.VALID_EVENT_TYPES`, retrieve each event count, and sum the results.
5. Add the total to the response under `safety_events_last_hour`, while handling Redis or monitoring errors gracefully.
6. Run Ruff, Black, and mypy on the staged files and verify the endpoint still returns a healthy response.

### Inputs & outputs

Inputs:
- The Redis connection URL from application settings.
- Redis counters using the key format `safety:events:<event_type>`.
- The valid event types defined by `SafetyMonitor.VALID_EVENT_TYPES`.

Output:
- The `/health` endpoint returns a JSON response containing:

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 0,
  "timestamp": "..."
}