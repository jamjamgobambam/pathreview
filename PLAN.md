## Solution plan

**Issue:** Add a safety event count to the health check endpoint — https://github.com/ascherj/pathreview/issues/68

### Understand
The `/health` endpoint already has a `safety_events_last_hour` field in its response, but it's hardcoded to 0 (see the "placeholder" comment in `api/routes/health.py`). It never queries the actual safety monitoring system. Meanwhile, `safety/monitoring.py` already has a working `SafetyMonitor` class with a `get_event_count(event_type, window_hours=1)` method backed by Redis. Expected behavior: the field should reflect real safety activity. Actual behavior: it always reports 0, regardless of how many safety events have fired.

### Map
- `api/routes/health.py` — the `health_check()` handler; replace the hardcoded `0` with a real call
- `safety/monitoring.py` — the `SafetyMonitor` class, specifically `get_event_count()` and the `VALID_EVENT_TYPES` set
- Wherever `SafetyMonitor` is instantiated/wired into the app (need to trace this — likely `core/` or app startup) to get access to it inside the health route

### Plan
1. Trace how `SafetyMonitor` is instantiated elsewhere in the app (e.g. in the safety layer or dependency injection) so I can access it from `health.py`, the same way `get_db` is used
2. Add a method or loop in `health.py` that sums `get_event_count(event_type)` across all 5 `VALID_EVENT_TYPES`, since `get_event_count` only handles one type at a time
3. Fix the "last hour" mismatch: `get_event_count`'s `window_hours` parameter is currently not enforced — Redis keys expire after 24 hours flat, not 1. Decide whether to implement real hourly windowing (e.g. time-bucketed Redis keys) or rename the field/behavior to be accurate
4. Replace the placeholder block in `health_check()` with the real total count
5. Add a test or manual check confirming the field updates after a safety event fires

### Inputs & outputs
**Input:** No new external input — this reads existing Redis state written by `SafetyMonitor.log_event()`.
**Output:** The `/health` response's `safety_events_last_hour` field changes from a hardcoded `0` to a real integer reflecting actual safety event counts.

### Risks & unknowns
- `get_event_count`'s docstring admits `window_hours` "is not enforced" — the underlying Redis key uses a flat 24-hour expiry (`self.redis.expire(key, 86400)`), not an actual 1-hour window. Naming the field `safety_events_last_hour` while it may reflect a 24-hour count is misleading; I need to decide whether to fix the windowing logic or adjust the field's meaning/name.
- I haven't yet found where `SafetyMonitor` gets instantiated with a Redis client in the app — I need to trace that before I know how to inject it into `health.py` (it currently only depends on `get_db`, not Redis).
- Redis itself can be down (the health check already handles a Redis-unhealthy case separately) — need to decide what `safety_events_last_hour` should return if Redis is unreachable, without crashing the whole health check.

### Edge cases
- Redis is unreachable when `/health` is called — should return a fallback value (e.g. `null` or `-1`) rather than throwing, since the rest of `/health` already tolerates partial dependency failure.
- No safety events have ever occurred — `get_event_count` should return `0` cleanly (already handled: `return int(count) if count else 0`).
- An unknown/invalid event type somehow gets summed — `log_event` already guards against unknown types by warning and returning early, so counts should stay consistent, but worth confirming no orphaned Redis keys from earlier bad data skew the total.