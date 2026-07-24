# Solution plan

**Issue:** [Add a safety event count to the health check endpoint](https://github.com/ascherj/pathreview/issues/68)

### Understand

The `/api/health` endpoint already includes a `safety_events_last_hour` field, but the current implementation hardcodes that value to `0` instead of pulling real counts from the monitoring layer. The expected behavior is for the health response to report the total number of safety events across all valid safety event types. The fix should preserve the existing health check behavior for dependencies while replacing the placeholder value with a computed count.

### Map

The main files and functions involved are:

- `api/routes/health.py` – the `health_check()` function assembles the health response and currently returns a placeholder value for `safety_events_last_hour`.
- `safety/monitoring.py` – the `SafetyMonitor.get_event_count()` method retrieves Redis-backed event counts and will be extended or reused to compute the total across all valid safety event types.
- `tests/` – the unit tests covering the health endpoint and safety monitoring behavior will be updated or expanded to verify the new functionality.

I expect to modify the `health_check()` function and the `SafetyMonitor` helper, then add or update unit tests to validate the implementation.

### Plan

1. Add a helper in `safety/monitoring.py` that computes the total safety event count across all entries in `VALID_EVENT_TYPES`.
2. Reuse the existing `get_event_count()` method inside that helper instead of duplicating Redis access logic.
3. Update `api/routes/health.py` to call the new helper and assign the returned total to `safety_events_last_hour`.
4. Add or update unit tests to confirm the health endpoint returns the computed total and still behaves correctly when there are no safety events.
5. Check error handling so the endpoint stays stable if Redis or the monitor layer is unavailable.

### Inputs & outputs

The fix takes the existing Redis backed safety event counts as input. Each valid event type already has a counter key managed by `SafetyMonitor`. The output should be the total count across all valid safety event types, returned from the health endpoint as `safety_events_last_hour`.

### Risks & unknowns

The current Redis design stores per type counters with an expiry, so the reported number may reflect retained event counts rather than a strict sliding one hour window. I need to confirm whether the current project expects a simple total over the retained safety counters or a true timestamp based last hour calculation. Another risk is introducing extra Redis calls if the helper loops over every valid event type, so I should keep the implementation small and reuse the existing monitor methods.

### Edge cases

The fix should handle an empty Redis state by returning `0`. It should also handle unknown or invalid event types by ignoring them, since only `VALID_EVENT_TYPES` should contribute to the health metric. If the monitoring layer cannot be reached, the health endpoint should fail gracefully in the same style as the rest of the health check logic.
