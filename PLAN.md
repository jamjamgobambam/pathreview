## Solution plan

**Issue:** Add a safety event count to the health check endpoint — [Issue #68 link]

### Understand

The health check response includes a `safety_events_last_hour` field, but before the fix this value was initialized to `0` and was never updated.

The expected behavior is for the `/health` endpoint to return the actual number of safety events recorded during the previous hour.

The actual behavior was that the endpoint always returned `0`, even when recent safety events existed.

The root cause is that `api/routes/health.py` did not use `SafetyMonitor` to retrieve recent event data from Redis. The existing monitoring implementation also needed a reliable way to store timestamped safety events so they could be counted within a rolling one-hour window.

### Map

The following files are involved:

- `api/routes/health.py`
  - Builds the health check response.
  - Connects to Redis.
  - Needs to retrieve and return the recent safety event count.

- `safety/monitoring.py`
  - Records safety events in Redis.
  - Needs to store timestamped events.
  - Needs a method for counting events within a requested time window.

- `tests/unit/test_health.py`
  - Tests that the health endpoint includes the correct safety event count.
  - Verifies that the monitoring method is called with a one-hour window.

- `tests/unit/test_safety_monitoring.py`
  - Tests the rolling-window event-counting logic.
  - Tests Redis error handling.

### Plan

1. Update `SafetyMonitor.log_event()` in `safety/monitoring.py` to store each safety event in a Redis sorted set using its timestamp as the score.

2. Add a `get_recent_event_count(window_hours=1)` method to `SafetyMonitor` that:
   - Calculates the start of the requested time window.
   - Removes events older than the retention period.
   - Uses Redis to count events within the requested time range.
   - Returns `0` if Redis raises an exception.

3. Update `api/routes/health.py` to create a `SafetyMonitor` using the existing Redis client and populate `safety_events_last_hour` using `get_recent_event_count(window_hours=1)`.

4. Add or update tests in `tests/unit/test_health.py` to verify that the health endpoint returns the count provided by `SafetyMonitor`.

5. Add or update tests in `tests/unit/test_safety_monitoring.py` to verify normal counting behavior and graceful handling of Redis failures.

### Inputs & outputs

**Inputs:**

- Safety events recorded through `SafetyMonitor.log_event()`.
- Event timestamps stored in Redis.
- A time-window value, with the health endpoint using one hour.
- A working Redis connection.

**Outputs:**

- The `/health` endpoint returns an integer in `safety_events_last_hour`.
- The integer represents the number of safety events recorded during the previous hour.
- If no recent events exist, the value is `0`.
- If Redis fails, the monitoring method returns `0`, while the health endpoint continues to use its existing dependency-health behavior.

### Risks & unknowns

- Redis may be unavailable when the health endpoint is called. The existing Redis health-check error handling in `api/routes/health.py` must remain consistent.

- Timestamp boundaries could cause events exactly at the beginning or end of the one-hour window to be counted incorrectly. The Redis score range needs to use consistent timestamp values.

- Old sorted-set entries could accumulate if they are not removed or expired. `safety/monitoring.py` should apply an expiration and remove events outside the retention period.

- The existing per-event counters must continue to work after timestamped event storage is added.

- Some unrelated tests in the repository are currently failing. Testing for this issue should focus on `tests/unit/test_health.py` and `tests/unit/test_safety_monitoring.py`.

### Edge cases

- No safety events have been recorded.
- One safety event occurred within the previous hour.
- Multiple safety events of different types occurred within the previous hour.
- Events exist but are older than one hour.
- An event occurs exactly on the time-window boundary.
- Redis returns no matching sorted-set entries.
- Redis raises an exception while counting or removing events.
- An invalid safety event type is passed to `log_event()`.
- The health endpoint is called while Redis is unavailable.
