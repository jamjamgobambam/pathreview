## Solution plan

**Issue:** Add a safety event count to the health check endpoint - https://github.com/ascherj/pathreview/issues/68

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- The root cause is that the `/health` route is currently a placeholder for safety monitoring: it initializes `safety_events_last_hour` to `0` and never queries the monitoring layer for recent activity.
- Expected behavior: the health endpoint should return a numeric `safety_events_last_hour` value that reflects the number of safety events recorded in the most recent hour.
- Actual behavior: the health response always reports `0` because the endpoint does not read from the Redis-backed monitoring state.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
- `api/routes/health.py` — builds the health payload and should populate `safety_events_last_hour` from the monitoring subsystem.
- `safety/monitoring.py` — implements Redis-backed safety event logging and should expose a rolling 1-hour count instead of a single hardcoded counter.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Reproduce the bug by inspecting the health response contract and confirming that `safety_events_last_hour` is hardcoded to `0`.
2. Update the monitoring implementation so safety events are stored in a way that supports a true rolling one-hour count.
3. Update the health endpoint to call the monitoring helper and return the real count in the response payload.
4. Add targeted regression tests that verify the rolling-window count and confirm the endpoint field is populated correctly.
5. Verify the fix by running the relevant unit test(s) and checking that the endpoint no longer returns a placeholder value.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- Input: the Redis-backed safety event stream produced by `SafetyMonitor.log_event()` and the existing health endpoint request path.
- Output: the `/health` response should include `safety_events_last_hour` as an integer representing all safety events recorded in the last hour.
- If Redis is unavailable or a count cannot be computed, the endpoint should gracefully fall back to `0` and log the error instead of crashing.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- The current monitoring code only stores a simple count with a 24-hour TTL, so it does not accurately represent the last hour by itself.
- The health route must avoid introducing a new dependency failure path for the health endpoint when Redis is temporarily unavailable.
- The implementation should preserve the existing health-check structure and avoid larger changes to unrelated API behavior.

### Edge cases
What inputs or states should your fix handle gracefully?
- No safety events exist in Redis for the last hour → return `0`.
- Redis is down or the count query raises an exception → log the failure and return `0` instead of failing the whole health check.
- Multiple safety event types are present → aggregate their counts into the total for the last hour.
- Old event timestamps should naturally age out of the rolling window so the count remains accurate over time.

### Test strategy
How should this change be validated?
- Add a unit test for `safety/monitoring.py` that verifies `get_event_count()` uses a rolling one-hour window and returns the expected numeric total.
- Add a unit test that ensures `log_event()` stores entries in a timestamped structure compatible with that rolling-window count.
- If the repository already has endpoint-level tests, add one assertion that `safety_events_last_hour` reflects the computed count instead of remaining hardcoded.
- The completion criterion is: the health endpoint returns a non-placeholder numeric value for `safety_events_last_hour`, and the targeted regression tests pass.