## Solution plan

**Issue:** [#68 — Add a safety event count to the health check endpoint](https://github.com/ascherj/pathreview/issues/68)

### Understand
The `/health` endpoint is meant to report operational signals about the service,
including how many safety events (PII detections, injection attempts, content
filtering, etc.) have occurred recently. Today the response always reports
`safety_events_last_hour: 0`.

- **Root cause:** In `api/routes/health.py` the field is set to a hardcoded `0`
  in two places (the initial `health_status` dict on line 25, and again in the
  "Count safety events" block on lines 75–80). The comment on line 77 even says
  *"This would be populated by actual safety event logging"* — it was never
  wired up.
- **Expected behavior:** The field should reflect the real number of safety
  events recorded over the last hour, read from the same Redis counters that
  `SafetyMonitor` maintains.
- **Actual behavior:** The field is always `0`, so the endpoint hides real
  safety activity and gives operators a false "all quiet" signal.
- The data already exists: `safety/monitoring.py` stores per-type counters in
  Redis (`SafetyMonitor.log_event`) and exposes `get_event_count(event_type)`
  to read them. Nothing consumes those counters yet.

### Map
Files, functions, and modules involved:

- **`safety/monitoring.py`** — `SafetyMonitor` class.
  - `VALID_EVENT_TYPES` (set of the 5 tracked event types).
  - `get_event_count(event_type, window_hours=1)` — reads a single type's count
    from Redis. There is no aggregate/total helper yet; I expect to add one.
- **`api/routes/health.py`** — `health_check()` endpoint.
  - Lines 25 and 75–80 (the hardcoded `safety_events_last_hour`).
  - Lines 39–56 already build a `redis.Redis(...)` client for the Redis health
    check; that client (or an equivalent) is what a `SafetyMonitor` needs.
- **`core/config.py`** — `settings.redis_host` / `settings.redis_port`, already
  used by the endpoint to construct the Redis client.

Files I expect to touch: `safety/monitoring.py` and `api/routes/health.py`
(plus a new/updated test under `tests/`).

### Plan
Break the fix into concrete sub-tasks:

1. **Add an aggregate helper to `SafetyMonitor`.** Add
   `get_total_event_count(window_hours=1)` (and/or `get_all_event_counts()`)
   that sums `get_event_count()` across `VALID_EVENT_TYPES` and returns the
   total, so the endpoint doesn't have to know the individual key names.
2. **Wire the helper into the health endpoint.** In `health_check()`, reuse the
   Redis client already created for the Redis check to build a `SafetyMonitor`,
   then replace the hardcoded `0` on lines 25 and 78 with a call to the new
   helper.
3. **Make it fail-safe.** Wrap the count in the existing try/except so that if
   Redis is unavailable the endpoint still returns (falling back to `0` for the
   count) and Redis being down is already reflected in `dependencies.redis`
   rather than crashing the health check.
4. **Add a regression test.** Add a test (e.g.
   `tests/integration/test_health_safety_events.py`) using a fake/mock Redis:
   log N events via `SafetyMonitor`, call the endpoint, assert
   `safety_events_last_hour == N`. This locks in the fix and mirrors the
   reproduction.

### Inputs & outputs
- **Input:** The per-type safety counters stored in Redis under
  `safety:events:<event_type>` keys (populated by `SafetyMonitor.log_event`),
  read via a Redis client built from `settings.redis_host` / `redis_port`.
- **Output:** The `safety_events_last_hour` integer in the `/health` JSON
  response now equals the real aggregate count instead of a constant `0`. No
  change to the HTTP status logic, the other dependency checks, or the response
  shape — only the value of that one field changes.

### Risks & unknowns
- **"Last hour" is not actually enforced.** `get_event_count()` ignores its
  `window_hours` argument (the docstring says so), and `log_event` sets a
  **24-hour** expiry on the Redis keys (line 51), so the counters really cover
  up to 24 hours, not one hour. The field name promises a 1-hour window the
  data can't back yet — I need to decide whether to (a) keep the field name and
  document the approximation, or (b) implement a true rolling 1-hour window
  (e.g. per-minute buckets / sorted sets). Risk of scope creep here; I'll likely
  do (a) for this fix and note (b) as follow-up.
- **Redis client lifecycle.** The Redis client is created inside a `try` block
  (lines 44–49); I must make sure the `SafetyMonitor` gets a valid client and
  that a Redis outage degrades gracefully instead of raising.
- **`decode_responses=True`** on the health endpoint's client vs. what
  `SafetyMonitor.get_event_count` expects — `int(count)` works on both `bytes`
  and `str`, so this is probably fine, but worth confirming.
- **Unknown:** whether other callers already construct a `SafetyMonitor` I
  should reuse, and where the canonical Redis client should live (DI vs. ad-hoc
  construction in the endpoint).

### Edge cases
- **Redis is down / unreachable** → endpoint must still respond; count falls
  back to `0` and `dependencies.redis` is marked `unhealthy` (no crash).
- **No events ever logged** → keys don't exist; `get_event_count` returns `0`;
  total is `0` (legitimately, not as a bug).
- **Keys expired** (older than the TTL) → treated as `0`, which is correct.
- **A non-integer / corrupted value in a key** → `int(count)` could raise;
  `get_event_count` already catches and returns `0` per type, so one bad key
  shouldn't zero out the whole total.
- **New event type added to `VALID_EVENT_TYPES` later** → the aggregate helper
  iterates the set, so it picks up new types automatically without touching the
  endpoint.
