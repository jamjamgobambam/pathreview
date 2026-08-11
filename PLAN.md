## Solution plan

**Issue:** [Add a safety event count to the health check endpoint (#68)](https://github.com/ascherj/pathreview/issues/68)

### Understand

The `/health` endpoint is supposed to report how many safety events (PII detections, injection attempts, content filtering, bias detections, rate limiting) occurred in the last hour, so operators can monitor safety activity without opening the dashboard. Instead, `safety_events_last_hour` in the response is hardcoded to `0` at [api/routes/health.py:78](api/routes/health.py#L78) — it never reads real data.

`safety/monitoring.py` already has a working `SafetyMonitor` class: `log_event()` increments a Redis counter per event type (`safety:events:{event_type}`, flat 24h TTL), and `get_event_count(event_type, window_hours=1)` reads that counter back — but it accepts `window_hours` and never actually uses it, so it can't answer "how many in the last hour" accurately even if it were called. Nothing in the codebase currently calls `SafetyMonitor` at all — it's implemented but never wired in.

Expected: `/health` returns a `safety_events_last_hour` count reflecting real events from roughly the last hour.
Actual: always `0`.

### Map

Files to touch:
- **`api/routes/health.py`** — replace the hardcoded `0` at line 78 with a real call into `SafetyMonitor`.
- **`safety/monitoring.py`** — `SafetyMonitor.log_event()` / `get_event_count()` need a real rolling-window implementation so `window_hours` is honored.

Reference only (not modified): **`safety/rate_limiter.py`**'s `RateLimiter.check_rate_limit()` already implements a Redis sorted-set rolling window (`ZADD` timestamp-scored members, `ZREMRANGEBYSCORE` to prune, `ZCARD` to count) — a good template to mirror. **`tests/unit/test_rate_limiter.py`** shows the existing test conventions (mocked `redis.Redis`, `@pytest.mark.unit`) to follow.

### Plan

1. Convert `SafetyMonitor.log_event()` to record events in a Redis sorted set per event type (`safety:events:{event_type}`, member = unique id, score = timestamp) instead of a flat `INCR` counter.
2. Update `SafetyMonitor.get_event_count()` to prune entries older than `window_hours` (`ZREMRANGEBYSCORE`) and return the live count (`ZCARD`), so `window_hours` actually does something.
3. Add logic to sum counts across all `VALID_EVENT_TYPES` into a single aggregate figure, since the health response field is singular (`safety_events_last_hour`), not per-type.
4. Wire `SafetyMonitor` into `api/routes/health.py`: construct it with the existing Redis client, call the aggregate count method, and replace the hardcoded `0` at line 78.
5. Add unit tests for `SafetyMonitor` (mirroring `test_rate_limiter.py`'s mocked-Redis style) covering the rolling window and aggregate count, and verify manually against the running local backend the same way the bug was reproduced.

### Inputs & outputs

**Input:** Safety events logged via `SafetyMonitor.log_event(event_type, details)`.
**Output:** The `/health` JSON response's `safety_events_last_hour` field — the sum of real event counts across all `VALID_EVENT_TYPES` within the last rolling hour, instead of a hardcoded `0`.

### Risks & unknowns

- **Nothing currently calls `SafetyMonitor.log_event()` anywhere in the app**, so even after this fix the field may show `0` in practice until other safety modules (bias detector, PII scrubber, prompt defense, rate limiter) start logging events. Need to decide if that wiring belongs in this PR or is a separate follow-up.
- **Changing the Redis data structure** (counter → sorted set) changes the shape of the `safety:events:{event_type}` key. Confirmed via grep that nothing else reads it directly, but worth re-checking before merging.
- **Redis unavailability:** `get_event_count()` currently swallows exceptions and returns `0` on Redis errors ([safety/monitoring.py:72-74](safety/monitoring.py#L72-L74)) — must preserve that fail-safe behavior so a Redis outage doesn't break `/health` itself.
- **Clock source:** `RateLimiter` uses `time.time()` for sorted-set scores; matching that (rather than `datetime.utcnow()`) keeps timestamp handling consistent across the two modules.

### Edge cases

- No events logged in the last hour → count should be `0` (current default output; must not regress).
- Events logged just outside the 1-hour boundary → must be excluded from the count (this is the core bug being fixed — there's currently no boundary at all).
- Unknown/invalid event type passed to `log_event()` → already handled today (logged as a warning and ignored); must remain unchanged.
- Redis connection failure at count-read time → `/health` should still respond rather than crash.
- High event volume → sorted-set reads should stay cheap (`ZCARD` after pruning), avoiding unbounded scans.
