# Solution plan

**Issue:** Add a safety event count to the health check endpoint — https://github.com/ascherj/pathreview/issues/68

### Understand

**Root cause.** The `/health` endpoint exposes a `safety_events_last_hour` field,
but it is **hardcoded to `0`**. In [api/routes/health.py](api/routes/health.py)
the field is set to `0` at line 25 and again at line 78, where the comment openly
calls it a *"placeholder"* that *"would be populated by actual safety event
logging."* The endpoint never talks to `SafetyMonitor` — the class that actually
records safety events in Redis — so the two are disconnected.

**Expected vs. actual.**

| | Expected | Actual |
|---|---|---|
| `safety_events_last_hour` | Reflects the number of recent safety events (PII detections, injection attempts, content filtering, etc.) | Always `0`, regardless of activity |
| Data source | Endpoint reads counts from `SafetyMonitor` / Redis | Endpoint reads nothing; value is a literal |

Reproduced in `tests/unit/test_health_safety_events_reproduction.py`: `SafetyMonitor`
records and counts events correctly, but the endpoint still returns `0`.

### Map

Files I expect to touch:

- **[safety/monitoring.py](safety/monitoring.py)** — add a method that totals events
  across *all* event types (today `get_event_count` handles one type at a time),
  e.g. `get_total_event_count(window_hours=1)` that iterates `VALID_EVENT_TYPES`
  and sums `get_event_count`.
- **[api/routes/health.py](api/routes/health.py)** — replace the hardcoded `0`
  (lines 25/78) with a real call into `SafetyMonitor`, using a Redis client built
  from the same settings the endpoint already uses for its Redis health check.
- **[tests/unit/test_health_safety_events_reproduction.py](tests/unit/test_health_safety_events_reproduction.py)**
  — remove the `xfail` marker once the fix lands (the reproduction becomes the
  regression test); add unit tests for the new `SafetyMonitor` method.

Read for context (may not modify): [core/config.py](core/config.py) — where Redis
connection settings (`redis_host`, `redis_port`) live.

### Plan

1. **Add a total-count method to `SafetyMonitor`.** `get_total_event_count(window_hours=1)`
   sums `get_event_count(t)` over `VALID_EVENT_TYPES`, returning `0` (not raising)
   if Redis is unavailable.
2. **Decide how to handle the "last hour" semantics** (see Risks). For a Tier-1
   scope, either implement true one-hour windowing with Redis sorted sets keyed by
   timestamp, or keep the existing rolling counter and make the field's meaning
   honest. I'll settle this with a mentor before coding Week 9.
3. **Wire the endpoint.** In `health_check`, construct a `SafetyMonitor` from the
   Redis client and set `safety_events_last_hour = monitor.get_total_event_count()`,
   wrapped in a `try/except` so a safety-count read failure logs and defaults to `0`
   instead of turning the whole health check into a 503.
4. **Update tests.** Remove the `xfail`; add unit tests for the new method (no
   events → 0, multiple types summed, Redis error → 0).
5. **Verify end-to-end.** Run `make test-unit` and `make check`, then manually hit
   `/health` after logging a few safety events and confirm the count is non-zero.

### Inputs & outputs

- **Input:** the per-type safety-event counters `SafetyMonitor.log_event` writes to
  Redis under keys `safety:events:{event_type}`.
- **Output / change:** the `/health` JSON's `safety_events_last_hour` becomes an
  integer reflecting recent safety events instead of a constant `0`. Dependency
  status and the overall healthy/unhealthy (200/503) behavior are unchanged.

### Risks & unknowns

- **"Last hour" isn't really tracked.** `SafetyMonitor.get_event_count` ignores its
  `window_hours` argument (docstring: *"not enforced here"*), and the counter has a
  24-hour TTL — so it's a rolling count, not a true one-hour window. Risk: the field
  name `safety_events_last_hour` would be misleading. Deciding scope (implement real
  windowing vs. document the limitation) is my biggest open question.
- **Redis availability.** Reading counts can raise if Redis is down. The read must
  default to `0` and log, and must **not** escalate into a 503 for the whole
  endpoint — needs a dedicated `try/except` in `health.py`.
- **Same Redis connection.** The endpoint builds its own Redis client inline; I must
  ensure `SafetyMonitor` reads from the *same* connection settings (`core/config.py`)
  that `log_event` writes to, or the counts won't match.
- **Existing `/health` consumers.** Need to grep tests / frontend for anything that
  asserts `safety_events_last_hour == 0`, so the change doesn't break a fixture.

### Edge cases

- No safety events yet → returns `0` cleanly (not an error).
- Redis unavailable or a key read fails → default to `0`, log, keep the health check working.
- Only some event types have counts → the total still sums correctly across all types.
- Counter keys have expired (TTL elapsed) → treated as `0`.
- Unknown/invalid event types recorded elsewhere → ignored; only `VALID_EVENT_TYPES` are summed.
- Very large counts → still returned as a plain integer.
