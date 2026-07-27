## Solution plan

**Issue:** The `/health` API endpoint returns service status but doesn't surface safety metrics — [issue #68](https://github.com/ascherj/pathreview/issues/68)

### Understand

**Root cause.** The `/health` endpoint already declares a `safety_events_last_hour`
field, but it is a hardcoded placeholder. In [`api/routes/health.py`](api/routes/health.py)
the value is set to `0` at initialization (line 25) and re-set to `0` again in a
try/except block (lines 75–80) with a comment reading *"This would be populated by
actual safety event logging."* The endpoint never consults the safety monitoring
subsystem, so the number is always `0` regardless of real activity.

Meanwhile [`safety/monitoring.py`](safety/monitoring.py) already tracks real counts:
`SafetyMonitor.log_event()` increments a per-event-type Redis counter
(`safety:events:<event_type>`), and `SafetyMonitor.get_event_count(event_type)`
reads it back. The data exists — nothing wires it into the health response.

**Expected vs. actual.**
- *Expected:* `safety_events_last_hour` reflects the number of safety events
  recorded by `SafetyMonitor` in the last hour (sum across all event types).
- *Actual:* `safety_events_last_hour` is always `0`.

This is confirmed by the reproduction test in
[`tests/unit/test_health_route.py`](tests/unit/test_health_route.py): with the
monitor holding 7 events, the endpoint still reports `0` (`assert 0 == 7`).

### Map

Files/functions involved:

- [`api/routes/health.py`](api/routes/health.py) — `health_check()`. Replace the
  hardcoded `safety_events_last_hour = 0` with a real read from the safety monitor.
  **(will touch)**
- [`safety/monitoring.py`](safety/monitoring.py) — `SafetyMonitor`. Add a helper
  that returns the total count across all `VALID_EVENT_TYPES` for a time window,
  since `get_event_count()` today only returns one event type at a time.
  **(will touch)**
- [`tests/unit/test_health_route.py`](tests/unit/test_health_route.py) — the
  reproduction test; extend it into the passing "green" test for the fix.
  **(will touch)**

### Plan

1. **Add a total-count helper to `SafetyMonitor`** in `safety/monitoring.py`:
   `get_total_event_count(window_hours: int = 1) -> int` that sums
   `get_event_count(t, window_hours)` over `VALID_EVENT_TYPES` and returns the
   total, reusing the existing error handling (return `0` on failure).
2. **Wire it into the health route** in `api/routes/health.py`: add a small
   module-level helper (e.g. `get_safety_event_count()`) that builds a Redis
   client from `settings` and returns `SafetyMonitor(...).get_total_event_count(1)`.
3. **Replace the placeholder** at lines 75–80 so
   `health_status["safety_events_last_hour"] = get_safety_event_count()`, keeping
   the surrounding try/except so a monitoring failure logs and falls back to `0`
   without breaking the health check.
4. **Update the test** in `tests/unit/test_health_route.py` so it patches the new
   helper to return `7` and asserts the response surfaces `7` — turning the
   reproduction (red) into a regression test (green).
5. **Verify** with `make test-unit` and a manual `GET /health` against a running
   instance with seeded safety events.

### Inputs & outputs

- **Input:** the Redis-backed safety counters (`safety:events:*` keys) populated
  by `SafetyMonitor.log_event()`, plus Redis connection details from `settings`.
- **Output:** the `/health` JSON response gains a truthful integer
  `safety_events_last_hour` = sum of safety events in the last hour. No change to
  the response shape, HTTP status semantics, or any other field.

### Risks & unknowns

- **Redis unavailability.** The safety counters live in Redis. If Redis is down,
  the safety-count read must not turn a healthy check into a 503. Mitigation: keep
  the count inside its own try/except (as today) and fall back to `0` on error —
  the existing Redis *dependency* probe already reports Redis health separately.
- **Redis client construction.** `health_check()` today builds its probe client
  with `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`,
  while `core/config.py` exposes `redis_url` (not `redis_host`/`redis_port`).
  I need to confirm which attributes actually resolve at runtime and construct the
  monitor's client consistently (likely `redis.from_url(settings.redis_url)`).
  This is an investigation path in `api/routes/health.py` + `core/config.py`.
- **"Last hour" semantics.** `SafetyMonitor` counters use a 24h expiry and are not
  strictly windowed to one hour (`window_hours` is documented as "not enforced").
  For this Tier-1 fix I will surface the existing counter value and keep the
  field name; a precise 1-hour rolling window is out of scope and noted as a
  follow-up.
- **decode_responses.** `get_event_count()` does `int(count)`; must confirm it
  works whether the client was created with `decode_responses=True` or not.

### Edge cases

- No safety events recorded yet → counters absent in Redis → count returns `0`
  (already handled by `get_event_count`'s `if count else 0`).
- Redis unreachable during the safety-count read → log the error, return `0`,
  and still return a healthy `200` if the other probes pass.
- A malformed/non-integer counter value in Redis → caught by `get_event_count`'s
  except branch, returns `0`.
- Multiple event types populated → the total must be the **sum** across all
  `VALID_EVENT_TYPES`, not a single type.