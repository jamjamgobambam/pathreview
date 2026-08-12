# PathReview Issue #68 – Solution Plan

## Solution plan

**Issue:** Add a safety event count to the health check endpoint

GitHub Issue: https://github.com/ascherj/pathreview/issues/68

---

## Understand

The `/health` endpoint reports the status of the application's dependencies, but it does not accurately report recent safety activity.

Although the endpoint includes a `safety_events_last_hour` field, it always returns a placeholder value of `0` instead of the actual number of safety events that occurred during the previous hour.

While investigating the issue, I found that `SafetyMonitor` stores cumulative Redis counters using `INCR`, but it does not preserve timestamps for individual events. Because of this, the existing implementation cannot determine how many events occurred within a specific time window, even though `get_event_count()` accepts a `window_hours` parameter.

The expected behavior is for the health endpoint to return the real number of safety events recorded during the previous hour.

---

## Map

The primary files involved are:

### `api/routes/health.py`

Responsible for the `/health` endpoint.

This file currently:
- checks PostgreSQL health
- checks Redis health
- checks Vector DB health
- returns the API health response

It will need to retrieve the real safety event count instead of returning a placeholder.

### `safety/monitoring.py`

Contains the `SafetyMonitor` class.

This file currently:
- validates supported safety event types
- logs safety events
- stores Redis counters
- retrieves event counts

It will need additional functionality to support time-based event counting.

Additional files that may be referenced during implementation:

- `core/config.py`
- existing unit tests for the health endpoint or safety monitoring components

---

## Plan

1. Review how `SafetyMonitor` stores safety events and determine why the existing Redis implementation cannot support one-hour queries.

2. Update the event logging logic so each safety event is stored with timestamp information that can later be queried.

3. Add functionality to calculate the total number of safety events that occurred within a requested time window.

4. Modify the `/health` endpoint to retrieve the calculated safety event count and populate the `safety_events_last_hour` response field.

5. Verify that dependency health checks continue working correctly and confirm the endpoint returns the expected response when safety events are present or absent.

---

## Inputs & outputs

### Inputs

The solution uses:

- Redis safety event data
- Valid safety event types
- Timestamp information for each event
- A requested time window (one hour)

### Outputs

The solution should:

- store safety events in a format that supports time-based queries
- calculate the number of events that occurred during the previous hour
- return that value in the `/health` endpoint response

Example response:

```json
{
  "status": "healthy",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "vector_db": "healthy"
  },
  "safety_events_last_hour": 4
}
```

---

## Risks & unknowns

Potential risks include:

- The existing Redis counter implementation does not retain timestamps, so a different storage approach may be required.
- Changes to `SafetyMonitor` could affect any other code that depends on the existing Redis key structure.
- Redis connection failures should not cause unrelated dependency checks to fail.
- Existing unit tests may assume the previous implementation and may require updates.
- Event data should expire automatically so Redis does not continue growing indefinitely.

---

## Edge cases

The solution should handle:

- No safety events during the previous hour.
- Multiple events occurring within the same second.
- Several different safety event types occurring during the same hour.
- Events older than one hour that should not be counted.
- Invalid or unsupported event types.
- Redis being temporarily unavailable.
- Failures while calculating the safety event count without preventing the rest of the health endpoint from responding.