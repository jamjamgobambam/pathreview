# Solution plan

**Issue:** Add a safety event count to the health check endpoint —
https://github.com/jamjamgobambam/pathreview/issues/68

### Understand

**Root cause.** The `/health` endpoint in [api/routes/health.py](api/routes/health.py)
advertises a `safety_events_last_hour` field but assigns it a literal `0`
([health.py:25](api/routes/health.py#L25) and again at
[health.py:78](api/routes/health.py#L78), with a comment calling it a
"placeholder"). The endpoint never consults the component that actually tracks
this data: `SafetyMonitor` in [safety/monitoring.py](safety/monitoring.py),
whose `get_event_count()` reads real per-type counts from Redis.

**Expected vs. actual.**
- *Expected:* `safety_events_last_hour` reflects the real number of safety
  events (PII detections, injection attempts, content filtering, bias
  detections, rate limits) recorded recently.
- *Actual:* it is always `0`, so operators cannot tell whether the safety layer
  has been active — the field is misleading.

Reproduction is captured in
[tests/unit/test_health_safety_events.py](tests/unit/test_health_safety_events.py):
one test proves `SafetyMonitor` returns real non-zero counts, a second proves
the endpoint reports `0` regardless.

### Map

Files I expect to touch:

- **[api/routes/health.py](api/routes/health.py)** — replace the hardcoded `0`
  with a call that aggregates real safety-event counts; keep it wrapped so a
  Redis failure never breaks the health check.
- **[safety/monitoring.py](safety/monitoring.py)** — `SafetyMonitor` already
  exposes `get_event_count(event_type)` and `VALID_EVENT_TYPES`. Add a small
  aggregation helper (e.g. `get_total_event_count(window_hours=1)`) that sums
  across all valid event types, so the endpoint has one clean call.
- **[tests/unit/test_health_safety_events.py](tests/unit/test_health_safety_events.py)**
  — flip the reproduction assertion from "hardcoded 0" to "reflects the
  aggregated count," and add coverage for the aggregation helper and the
  Redis-failure fallback.

Supporting (read, likely not modified): [core/config.py](core/config.py) for the
Redis connection string, and how a Redis client is obtained for the endpoint.

### Plan

1. **Add aggregation to `SafetyMonitor`** — a `get_total_event_count()` method
   that sums `get_event_count()` over `VALID_EVENT_TYPES`, returning `0` on
   Redis error (mirroring the existing per-type error handling).
2. **Wire the endpoint** — in `health_check`, obtain a Redis client from
   `settings.redis_url`, build a `SafetyMonitor`, and set
   `safety_events_last_hour` from `get_total_event_count()`. Keep the existing
   `try/except` so any failure falls back to `0` instead of raising.
3. **Resolve the "last hour" semantics** — `get_event_count` currently ignores
   its `window_hours` argument ([monitoring.py:61](safety/monitoring.py#L61))
   and the Redis counters use a 24h TTL, so the count is cumulative, not a true
   rolling hour. Decide scope with the maintainer: relabel to match reality, or
   implement hourly bucketed keys. Document the decision in this file.
4. **Update and add tests** — flip the reproduction test to assert the real
   aggregated value; add a unit test for `get_total_event_count` and one
   asserting a Redis error yields `0` (health check stays resilient).
5. **Verify** — run `make check` and `make test-unit`; update PLAN.md/JOURNAL.md
   with the final approach.

### Decisions made during implementation (Week 9)

- **Window semantics (step 3) — deferred, not implemented.** A true rolling hour
  needs bucketed Redis keys, which would change `log_event`'s write path for
  every safety module, well beyond a tier-1 "good first issue". I kept the
  existing counters and documented precisely what the number means in the
  `get_total_event_count` and `health_check` docstrings. Flagged in the PR as a
  follow-up so the maintainer can decide between relabelling the field and
  implementing buckets.
- **Redis client wiring — fixed, because the change depends on it.** The
  endpoint built its client from `settings.redis_host`/`redis_port`, which
  `Settings` does not define, so the call raised `AttributeError` and no client
  ever existed to hand to `SafetyMonitor`. Switched to
  `redis.from_url(settings.redis_url)` and reused that one client for both the
  redis dependency check and the safety count. This also removes 3 pre-existing
  mypy errors in the file.

### Inputs & outputs

- **Input:** the Redis safety counters keyed `safety:events:{event_type}`,
  populated by `SafetyMonitor.log_event()` across the safety layer.
- **Output:** an integer `safety_events_last_hour` in the `/health` JSON
  response equal to the sum of those counters. The change must be
  non-breaking — the health endpoint must still succeed (and report `0` for
  this field) even when Redis is unavailable.

### Risks & unknowns

- **Redis client wiring is currently broken.** While reproducing, the redis
  health check raised `'Settings' object has no attribute 'redis_host'` — the
  endpoint reads `settings.redis_host`/`redis_port`, but
  [core/config.py:12](core/config.py#L12) only defines `redis_url`. My fix must
  use `redis.from_url(settings.redis_url)`. Whether to *also* fix the existing
  redis-health check is a scope question for the maintainer (I'll keep #68
  focused on the safety count and flag the adjacent bug separately).
- **Window semantics.** A true "last hour" needs bucketed keys; the current
  cumulative-with-24h-TTL counter is not that. This could balloon scope — I'll
  confirm the intended behavior before implementing buckets.
- **Resilience.** A Redis outage must not flip `/health` to 503 on account of
  the safety count; the count is best-effort and defaults to `0`.
- **Sync client in an async handler.** The existing code already calls a
  synchronous Redis client inside the async endpoint; I'll match that pattern
  rather than introduce async Redis in this change.

### Edge cases

- **Redis unavailable / connection refused** → return `0`, do not raise.
- **No events logged yet** (keys absent / expired) → `0`.
- **Counter stored as a string** in Redis → integer conversion (already handled
  by `get_event_count`).
- **Multiple event types present** → summed correctly across
  `VALID_EVENT_TYPES`.
- **Unknown/legacy keys** in Redis → ignored; only valid event types counted.
