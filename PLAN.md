## Solution plan

**Issue:** Add a safety event count to the health check endpoint —
https://github.com/ascherj/pathreview/issues/68

### Understand
The `/health` response advertises a `safety_events_last_hour` field so operators can
watch safety-system activity without opening the monitoring dashboard. But the field is
a **hardcoded `0`** in `api/routes/health.py` (set once in the initial dict at line ~25
and re-assigned to `0` in a placeholder `try` block at line ~78). It never consults the
safety subsystem, so it reports `0` no matter how many safety events have occurred.

- **Expected:** `safety_events_last_hour` reflects the real number of recent safety
  events recorded by the safety subsystem.
- **Actual:** always `0`.

The data already exists: `SafetyMonitor` (`safety/monitoring.py`) increments per-type
counters in Redis (`safety:events:<type>`, 24h TTL) on every `log_event`, and exposes
`get_event_count(event_type)`. The bug is purely that the endpoint doesn't read it — a
missing wiring, confirmed by the reproduction test (`test_health_surfaces_real_safety_event_count`
asserts `3` but gets `0`).

### Map
- **`api/routes/health.py`** — the endpoint. Replace the hardcoded `0` with a real
  count sourced from the safety subsystem. Needs a Redis client (build one from
  `settings.redis_url`).
- **`safety/monitoring.py`** — `SafetyMonitor` / `VALID_EVENT_TYPES` /
  `get_event_count()`. I plan to add a small `get_total_event_count()` helper here that
  sums across `VALID_EVENT_TYPES`, so the endpoint stays thin and the summing logic is
  unit-testable in the safety module.
- **`core/config.py`** — read-only reference; `settings.redis_url` is the connection
  source (note: `redis_host`/`redis_port` referenced elsewhere in health.py do **not**
  exist on `Settings` — see Risks).
- **`tests/unit/test_health_safety_events.py`** — the reproduction test (already added);
  it should flip from failing to passing once the fix lands.

### Plan
1. **Add `SafetyMonitor.get_total_event_count(window_hours=1) -> int`** in
   `safety/monitoring.py` that sums `get_event_count(t)` over `VALID_EVENT_TYPES`,
   wrapped in try/except so a Redis error returns `0` (never raises).
2. **Wire the endpoint:** in `api/routes/health.py`, construct a Redis client from
   `settings.redis_url` (via `redis.Redis.from_url`), instantiate `SafetyMonitor`, and
   set `health_status["safety_events_last_hour"] = monitor.get_total_event_count()`
   inside the existing safety `try/except` (replacing the placeholder `0`). Keep it
   non-fatal: a failure logs and leaves the count at `0`.
3. **Reuse a single Redis client** if practical — the redis dependency check and the
   safety count can share one client built from `redis_url`, reducing duplication.
4. **Confirm the reproduction test passes** and add a Redis-unavailable case asserting
   the count degrades to `0` without breaking the response.
5. **Run `make check` (ruff/black/mypy) and `make test-unit`**; update JOURNAL/PLAN.

### Inputs & outputs
- **Input:** the safety counters in Redis (keys `safety:events:<type>`), read via
  `SafetyMonitor`. No new request parameters; `/health` stays a parameterless GET.
- **Output:** the `safety_events_last_hour` value in the JSON response becomes the
  summed real count (an integer ≥ 0) instead of the constant `0`. No change to status
  codes or the `dependencies` block.

### Risks & unknowns
- **"Last hour" is not truly enforced by the data model.** The Redis counters are
  cumulative per-type with a **24-hour** TTL (`safety/monitoring.py` sets `expire(key,
  86400)`), and `get_event_count`'s `window_hours` arg is explicitly *not enforced*. So
  summing current counters approximates "recent activity," not a strict rolling 60-minute
  window. I need to decide (and document) whether to (a) ship the cumulative sum as-is
  and note the limitation, or (b) move to time-bucketed keys — (b) is larger scope than a
  Tier 1 fix, so I lean (a) with a clear docstring/field note.
- **Pre-existing Redis-config bug in `health.py`:** the dependency check reads
  `settings.redis_host` / `settings.redis_port`, which don't exist on `Settings` (only
  `redis_url`), so the Redis check currently always errors. My fix should source Redis
  from `redis_url`; I'll avoid *expanding* scope but must not depend on the broken
  attributes. (Flag to maintainer; possibly a follow-up issue.)
- **Sync Redis client inside an async endpoint** could block the event loop. The existing
  code already uses the sync `redis` client here, so I'll match the current pattern to
  keep the change minimal, and note async Redis as a possible follow-up.
- **Unknown:** whether maintainers want the sum across *all* event types or a subset —
  I'll assume all `VALID_EVENT_TYPES` and call it out in the PR.

### Edge cases
- **Redis down / connection error:** count must fall back to `0` and the health check
  must still return (never 500 because of the safety count).
- **No events recorded yet:** keys absent → `get_event_count` returns `0` → total `0`
  (unchanged, correct).
- **Counters expired (past 24h TTL):** keys gone → `0`, which is acceptable.
- **Unknown/new event type logged:** `log_event` already rejects types outside
  `VALID_EVENT_TYPES`, so the sum only covers known types — consistent and bounded.
- **Non-integer / corrupt Redis value:** `get_event_count` already guards with
  try/except and returns `0`; the total helper inherits that safety.
