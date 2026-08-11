## Solution plan

**Issue:** #68 , Add a safety event count to the health check endpoint
(https://github.com/ascherj/pathreview/issues/68)

### Understand
The `/health` endpoint already has a `safety_events_last_hour` field in its response
(`api/routes/health.py`, line ~25), but it's hardcoded to `0` inside a placeholder
block (lines 75-80) with a comment saying "This would be populated by actual safety
event logging." The real gap isn't the field itself , it's that nothing behind it
actually counts events by time window.

The root cause lives in `safety/monitoring.py`. `log_event()` (lines 30-54) stores
each event as a single flat Redis integer counter (`safety:events:{event_type}`,
incremented with `INCR`), with a flat 24-hour TTL reset on every call. There are no
per-event timestamps stored anywhere , a `timestamp` variable is computed on line 41
but never used. Because of this, `get_event_count(event_type, window_hours=1)`
accepts a `window_hours` parameter but structurally cannot honor it , it just reads
the one counter and returns it, regardless of the window requested (confirmed via
`reproduce_issue_68.py`).

Expected behavior: `get_event_count` should return only the count of events logged
within the requested window, and the health endpoint should surface a real
"events in the last hour" number instead of `0`.

**Root cause:** `log_event` uses a flat, non-timestamped Redis counter, so no
time-windowed query is possible on top of it.

### Map
Files I expect to touch:
- `safety/monitoring.py` , rewrite `log_event()` to store timestamped entries
  (Redis sorted set) instead of a flat `INCR` counter; rewrite `get_event_count()`
  to actually filter by `window_hours`.
- `safety/rate_limiter.py` , not modified, but used as the reference pattern:
  `RateLimiter.check_rate_limit()` (lines 21-63) already implements a sorted-set
  rolling window with `zremrangebyscore` + `zcard`/`zadd`, which I'll mirror for
  consistency.
- `api/routes/health.py` , replace the hardcoded placeholder block (lines 75-80)
  with a real call into `SafetyMonitor.get_event_count(...)`. Since the route
  currently builds its own inline `redis.Redis(...)` client for the ping (lines
  44-49) and has no `SafetyMonitor` instance, I'll need to instantiate one here.
- `tests/unit/test_monitoring.py` , new file (none exists yet). I'll follow the
  mocking style used in `tests/unit/test_rate_limiter.py`, which mocks Redis
  sorted-set methods with `Mock()`.
- `tests/unit/test_health.py` , new file (none exists yet), to test the wired-up
  health response field.

### Plan
1. Rewrite `log_event()` in `safety/monitoring.py` to write to a Redis sorted set
   instead of `INCR`. Use `time.time()` as the score (matching `rate_limiter.py`'s
   convention, not `datetime.utcnow().isoformat()`), with `zadd(key, {str(now): now})`.
   Use a new key name, e.g. `safety:events:z:{event_type}`, to avoid colliding with
   any existing flat-counter data under the old key name (avoids `WRONGTYPE` errors).
2. Rewrite `get_event_count()` to actually use `window_hours`: compute
   `window_start = time.time() - (window_hours * 3600)`, call
   `zremrangebyscore(key, 0, window_start)` to drop stale entries, then
   `zcard(key)` (or `zcount`) to get the count within the window. Set `expire()`
   to a bit beyond the window, matching `rate_limiter.py`'s pattern.
3. Update `api/routes/health.py`'s placeholder block (lines 75-80) to instantiate
   `SafetyMonitor` and call `get_event_count(event_type, window_hours=1)` for
   each relevant event type (need to decide: sum across all `VALID_EVENT_TYPES`,
   or track a single aggregate count , see Risks below), replacing the hardcoded
   `0`.
4. Write `tests/unit/test_monitoring.py`: test that `log_event` writes a
   timestamped entry, that `get_event_count` correctly excludes entries older
   than the window, and that it correctly includes entries within the window
   (mocking Redis the same way `test_rate_limiter.py` does).
5. Write `tests/unit/test_health.py`: test that the health response includes a
   real (non-hardcoded) `safety_events_last_hour` value, using a mocked
   `SafetyMonitor`.
6. Run `make test-unit` (or the repo's equivalent test command) to confirm
   nothing else breaks.
7. Manually re-run `reproduce_issue_68.py` (or an updated version of it) to
   confirm `get_event_count(window_hours=1)` and `get_event_count(window_hours=24)`
   now return different values when events are logged at different simulated
   times.

### Inputs & outputs
**Function I'm changing:** `log_event(event_type: str, details: dict) -> None`
- Existing behavior: increments a flat counter, no timing info stored.
- New behavior: writes a sorted-set entry scored by current Unix timestamp under
  key `safety:events:z:{event_type}`.

**Function I'm changing:** `get_event_count(event_type: str, window_hours: int = 1) -> int`
- Existing behavior: ignores `window_hours`, returns the flat counter value.
- New behavior: returns only the count of entries within the requested window,
  computed from the sorted set.

**Endpoint I'm changing:** `GET /health` (in `api/routes/health.py`)
- Existing behavior: `safety_events_last_hour` is always `0`.
- New behavior: reflects a real count from `SafetyMonitor.get_event_count(...)`
  called with `window_hours=1`.

### Risks & unknowns
1. **Key migration / `WRONGTYPE` risk**: switching `safety:events:{event_type}`
   from a Redis string (`INCR`) to a sorted set (`ZADD`) on the same key name
   would throw `WRONGTYPE` if any existing key still holds the old string value.
   I'm mitigating this by using a new key namespace (`safety:events:z:{event_type}`),
   but I should confirm with the team/mentor whether the old keys need active
   cleanup or can just expire naturally (they already have a 24h TTL).
2. **No existing callers to validate against**: a grep across `api/`, `safety/`,
   and `core/` shows nothing currently calls `log_event()` or `get_event_count()`
   in the request path. This means low risk of breaking other code, but also
   means `safety_events_last_hour` will show `0` in practice until something
   actually starts logging events , I need to check if there's a separate issue/
   TODO for wiring up actual event-logging call sites, since that's out of scope
   for #68 itself.
3. **Aggregation ambiguity**: `SafetyMonitor.VALID_EVENT_TYPES` likely has more
   than one event type (e.g. `pii_detected` and others) , I need to check the
   full list and decide whether `safety_events_last_hour` sums counts across all
   event types or reports a specific one. This isn't answered by the issue text
   and needs a design decision, possibly flagged to a mentor.
4. **No existing tests to check regressions against**: since `test_monitoring.py`
   and `test_health.py` don't exist yet, I'm writing the first tests for this
   code , there's a risk my tests encode assumptions that don't match how the
   maintainers intended this to behave. I'll keep test names and structure close
   to `test_rate_limiter.py`'s existing conventions to reduce this risk.

### Edge cases
- **No events logged at all**: `get_event_count` should return `0`, not error,
  when the sorted-set key doesn't exist yet (first-time / cold-start case).
- **Events exactly at the window boundary**: an event logged at exactly
  `window_hours` ago , need to decide inclusive vs exclusive boundary and test it
  explicitly (matching whatever `rate_limiter.py` does for consistency).
- **Redis connection failure during health check**: the health endpoint should
  fail gracefully (matching the existing `try/except` + `log.error(...)` pattern
  already in the placeholder block) rather than crashing the whole `/health`
  response if `get_event_count` throws.
- **Multiple event types logged in the same window**: if `safety_events_last_hour`
  aggregates across event types, a mix of `pii_detected` and other types within
  the hour should all be counted correctly, not just the first type checked.