## Solution plan

**Issue:** Add a safety event count to the health check endpoint — https://github.com/ascherj/pathreview/issues/68

### Understand
`health.py` hardcodes `safety_events_last_hour` to 0 and never calls `SafetyMonitor`. Even if it did, no detector currently calls `log_event()`, so Redis has no data to read.

### Map
- `api/routes/health.py` - replace hardcoded 0 with a real count.
- `safety/monitoring.py` - `get_event_count()` checks one event type at a time; needs aggregation across `VALID_EVENT_TYPES`.
- `safety/bias_detector.py`, `safety/pii_scrubber.py`, `safety/prompt_defense.py` - detect events but never call `log_event()`.
- `core/config.py` - `health.py` references `settings.redis_host`/`redis_port`, which don't exist (only `redis_url` does).

### Plan
1. Fix the `redis_host`/`redis_port` reference in `health.py` (parse from `redis_url`).
2. Add `log_event()` calls to the three detectors.
3. Replace the hardcoded 0 in `health.py` with `SafetyMonitor.get_event_count()`, summed across event types.
4. Update `tests/unit/test_health.py` to assert the fixed behavior.
5. Manually re-verify: trigger a PII detection, hit `/health`, confirm a nonzero count.

### Inputs & outputs
Input: existing safety-detection signals (PII, injection, bias, rate limiting). Output: `safety_events_last_hour` reflects real Redis counts instead of a hardcoded 0.

### Risks & unknowns
- Wiring the 3 detectors is beyond the issue's stated 2-4hr scope - confirm with a mentor whether it belongs in this PR.
- `get_event_count()`'s `window_hours` isn't enforced (per its own docstring); count reflects a 24h Redis TTL, not a true rolling hour.
- Check for an existing shared Redis client before adding a new one in `health.py`.

### Edge cases
- Zero events --> return 0, no error.
- Redis down -->  degrade the same way `/health` already does for other dependencies.
- Multiple event types firing at once --> decide aggregate vs. per-type count.
