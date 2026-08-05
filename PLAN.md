## Solution plan

**Issue:** #68 — Add a safety event count to the health check endpoint
https://github.com/Ahmadkarim7/pathreview/issues/68

### Understand
The `/health` endpoint already has a `safety_events_last_hour` key in its response, but it's
hardcoded to `0` inside a placeholder try block in `api/routes/health.py`:

```python
try:
    # This would be populated by actual safety event logging
    health_status["safety_events_last_hour"] = 0
except Exception as exc:
    log.error("safety_events_check_failed", error=str(exc))
```

It never calls into `safety/monitoring.py`'s `SafetyMonitor` class. So the field exists but
is disconnected from the actual safety event data.

`SafetyMonitor.get_event_count(event_type, window_hours=1)` looks like the intended source
of this data, but there are two problems with it as-is:
1. It only returns a count for **one** event type at a time. The health check needs a total
   across all 5 types in `VALID_EVENT_TYPES` (`pii_detected`, `injection_attempt`,
   `content_filtered`, `bias_detected`, `rate_limited`).
2. Its `window_hours` parameter is **not enforced** — the docstring says so explicitly.
   The underlying Redis key (`safety:events:{event_type}`) is incremented with `incr` and
   given a flat 24-hour expiry (`self.redis.expire(key, 86400)`). There's no per-hour
   bucketing, so a count returned "for the last hour" could really reflect events from up
   to 24 hours ago, until the key happens to expire.

**Root cause:** (a) `health.py` was never wired up to `SafetyMonitor`, and (b) even if wired
up, `SafetyMonitor` doesn't currently track events with real hourly granularity — only a
rolling 24h counter per event type.

### Map
Files I expect to touch:
- `api/routes/health.py` — replace the hardcoded `0` in the `safety_events_last_hour` block
  with a real call into `SafetyMonitor`. Need to figure out how the endpoint gets access to
  a Redis client / `SafetyMonitor` instance (it doesn't currently import either) — likely
  via a new FastAPI dependency, similar to how `db=Depends(get_db)` works.
- `safety/monitoring.py` — add a method (e.g. `get_total_event_count(window_hours=1)`) that
  sums across all `VALID_EVENT_TYPES`, and fix the Redis key scheme so `window_hours` is
  actually enforced (e.g. per-hour bucketed keys like `safety:events:{event_type}:{hour_bucket}`,
  or a sorted set with timestamps and `ZREMRANGEBYSCORE` to drop entries older than the window).
- Wherever the app's shared Redis client is created/injected (not yet located — need to
  search for existing `Depends(...)` patterns near `get_db` in `core/`, since `health.py`
  currently creates its own throwaway `redis.Redis(...)` instance inline just for the
  dependency check, rather than reusing a shared client).
- Test file for the health endpoint (location not yet confirmed — need to check for an
  existing `tests/.../test_health.py` or equivalent, or create one).

### Plan
1. Search the codebase for where `SafetyMonitor` is currently instantiated and where
   `log_event()` is called elsewhere (e.g., in middleware or other routes), to find the
   existing pattern for getting a Redis client / `SafetyMonitor` instance via dependency
   injection.
2. Decide on the Redis key redesign for real hourly windowing. Simplest approach: switch
   from a single `incr` counter to a Redis sorted set per event type
   (`safety:events:{event_type}:zset`), storing each event's timestamp as the score, with
   `ZREMRANGEBYSCORE` to prune anything older than `window_hours` before counting with
   `ZCARD`. This replaces `incr`/`expire` in `log_event()`.
3. Add `get_total_event_count(window_hours: int = 1) -> int` to `SafetyMonitor`, summing
   `get_event_count(event_type, window_hours)` (updated to use the new windowed logic)
   across all `VALID_EVENT_TYPES`.
4. Wire up `api/routes/health.py`: add a dependency to inject the shared `SafetyMonitor` (or
   Redis client), and replace the hardcoded `0` with
   `safety_monitor.get_total_event_count(window_hours=1)`. Keep the existing try/except so a
   Redis failure here degrades gracefully to `0` rather than marking the whole endpoint
   unhealthy — matching the current pattern.
5. Run existing tests to confirm nothing else breaks: `make test-unit` (or repo equivalent).
6. Write a new test that logs a safety event via `SafetyMonitor.log_event()`, then hits
   `/health`, and asserts `safety_events_last_hour` reflects it (see below).
7. Run `make check` (lint/format/types) if the repo has one.

### Inputs & outputs
**Function I'm changing:** `SafetyMonitor.get_event_count()` (fixing windowing) and adding
`SafetyMonitor.get_total_event_count()`; also `health_check()` in `health.py`.

**Existing happy path:** `/health` returns dependency statuses and a hardcoded
`safety_events_last_hour: 0`.

**New behavior:**
- Input: one or more safety events logged via `SafetyMonitor.log_event()` within the last
  hour.
- Expected output: `/health` response's `safety_events_last_hour` reflects the real count,
  summed across all event types, only counting events within the last hour.

**Test I'll write (exact location TBD once I find the test directory):**
```python
def test_health_reflects_recent_safety_events(client, safety_monitor):
    safety_monitor.log_event("content_filtered", {"reason": "test"})
    safety_monitor.log_event("rate_limited", {"reason": "test"})

    response = client.get("/health")

    assert response.json()["safety_events_last_hour"] == 2
```

### Risks & unknowns
1. **The `window_hours` fix is bigger than "add a field."** The issue's 2–4 hour estimate
   assumes the data already exists; enforcing real hourly windowing means redesigning the
   Redis storage (counter → sorted set), which touches `log_event()` too, not just the
   getter. I may raise this with a mentor to confirm whether a true rolling-hour count is
   expected, or whether a documented "approximate, resets every 24h" count is acceptable
   for this issue's scope.
2. **I haven't located how `health.py` should get a Redis client / `SafetyMonitor`
   instance.** It currently instantiates its own local `redis.Redis(...)` just to `.ping()`
   for the dependency check — I don't yet know if there's a shared client elsewhere I
   should reuse instead of creating a second connection.
3. **Someone else may be working this same issue.** I noticed another contributor
   (RadRebelSam) commented on issue #68 and pushed a branch with a name almost identical to
   mine. I'll confirm with the instructor/mentor before investing more time to avoid
   duplicate work.
4. **Redis sorted-set migration risk.** If `log_event()`'s storage format changes, I need to
   confirm nothing else in the codebase reads the old `safety:events:{event_type}` counter
   format directly (e.g., a dashboard or another endpoint), or I'll break it silently.

### Edge cases
- No safety events ever logged (Redis key doesn't exist) → total count should be `0`, not
  an error.
- Redis is down when `/health` is called → `safety_events_last_hour` should gracefully
  return `0` (matching existing `except` behavior in both `health.py` and
  `get_event_count`), without marking the whole `/health` response `"unhealthy"`.
- Events logged more than 1 hour ago but within the old 24h expiry window → must NOT be
  counted once the windowing fix is in place (this is the actual bug being fixed).
- Multiple event types logged in the same hour → total must sum across all of them, not
  just the first type checked.
- Unknown/invalid event type passed to `log_event()` → already handled upstream (logged as
  a warning and skipped); not part of this fix.