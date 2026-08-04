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
1. Fix the `redis_host`/`redis_port` reference in `health.py` (parse from `redis_url` via `redis.Redis.from_url`). Done.
2. ~~Add `log_event()` calls to the three detectors.~~ Descoped: grepped the repo and none of `BiasDetector`/`PIIScrubber`/`PromptDefense` are called anywhere outside their own tests, so the detectors aren't wired into the review flow at all yet. Making them log events wouldn't produce a meaningful count in production — that's a separate, larger issue (wiring the safety pipeline into review submission), not part of #68's stated scope (files listed: `api/routes/health.py`, `safety/monitoring.py`; 2-4hr estimate).
3. Replace the hardcoded 0 in `health.py` with `SafetyMonitor.get_event_count()`, summed across event types. Done.
4. Update `tests/unit/test_health.py` to assert the fixed behavior. Done — reproduction test now passes, plus added tests for zero-events, multi-type aggregation, and Redis-down degradation.
5. Manually re-verify: trigger a PII detection, hit `/health`, confirm a nonzero count. Still needed — requires a running Postgres/Redis locally, which I can't do from here.

### Inputs & outputs
Input: existing safety-detection signals (PII, injection, bias, rate limiting). Output: `safety_events_last_hour` reflects real Redis counts instead of a hardcoded 0.

### Risks & unknowns
- Resolved: descoped detector wiring (see Plan step 2) rather than confirming with a mentor, given the time constraint — flagging this decision for review in the PR description.
- `get_event_count()`'s `window_hours` isn't enforced (per its own docstring); count reflects a 24h Redis TTL, not a true rolling hour. Left as-is; noting as a known limitation in the PR rather than fixing, since it's a `safety/monitoring.py` behavior change beyond this issue.
- No existing shared Redis client found elsewhere in the app (confirmed via grep) — `health.py` now creates its own via `redis.Redis.from_url`, consistent with how it already handled the dependency-check client.
- Not yet verified against a real running Postgres/Redis — only unit-tested with fakes/mocks. Need to confirm end-to-end locally before considering this fix complete.

### Edge cases
- Zero events --> return 0, no error.
- Redis down -->  degrade the same way `/health` already does for other dependencies.
- Multiple event types firing at once --> decide aggregate vs. per-type count.
