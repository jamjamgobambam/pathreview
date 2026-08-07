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
  hardcoded `safety_events_last_hour = 0` with a real read from an **injected**
  `SafetyMonitor`, received via FastAPI's `Depends(...)` (the same mechanism the
  route already uses for `db`). The route does not build its own Redis client.
  **(will touch)**
- [`safety/monitoring.py`](safety/monitoring.py) — `SafetyMonitor`. Add
  (a) a `get_total_event_count(window_hours=1)` method that sums across all
  `VALID_EVENT_TYPES`, since `get_event_count()` today returns one type at a time,
  and (b) a `get_safety_monitor()` dependency provider that constructs the Redis
  client (`redis.from_url(settings.redis_url)`) and returns a `SafetyMonitor`.
  **(will touch)**
- [`tests/unit/test_health_route.py`](tests/unit/test_health_route.py) — the
  reproduction test; simplify it into the passing "green" test by passing a fake
  `SafetyMonitor` straight into `health_check()` (no `patch()` of Redis needed).
  **(will touch)**

### Plan

1. **Add a total-count method to `SafetyMonitor`** in `safety/monitoring.py`:
   `get_total_event_count(window_hours: int = 1) -> int` that sums
   `get_event_count(t, window_hours)` over `VALID_EVENT_TYPES` and returns the
   total, reusing the existing error handling (return `0` on failure).
2. **Add a dependency provider** `get_safety_monitor()` (in `safety/monitoring.py`)
   that constructs the Redis client via `redis.from_url(settings.redis_url)` and
   returns a `SafetyMonitor`. This keeps all Redis-connection logic in the safety
   module, not the route.
3. **Inject it into the health route** in `api/routes/health.py`: add a
   `monitor: SafetyMonitor = Depends(get_safety_monitor)` parameter to
   `health_check()` and replace the placeholder at lines 75–80 with
   `health_status["safety_events_last_hour"] = monitor.get_total_event_count(1)`,
   keeping the surrounding try/except so a monitoring failure logs and falls back
   to `0` without breaking the health check.
4. **Simplify the test** in `tests/unit/test_health_route.py` to call
   `health_check(db=..., monitor=fake_monitor)` with a fake monitor whose
   `get_total_event_count` returns `7`, and assert the response surfaces `7` —
   turning the reproduction (red) into a regression test (green) with no Redis
   patching.
5. **Verify** with `make test-unit` and a manual `GET /health` against a running
   instance with seeded safety events.

### Inputs & outputs

- **Input:** the Redis-backed safety counters (`safety:events:*` keys) populated
  by `SafetyMonitor.log_event()`, plus Redis connection details from `settings`.
- **Output:** the `/health` JSON response gains a truthful integer
  `safety_events_last_hour` = sum of safety events in the last hour. No change to
  the response shape, HTTP status semantics, or any other field. The route's new
  input is an injected `SafetyMonitor` dependency (via `Depends`), not a direct
  Redis connection.

### Risks & unknowns

- **Redis unavailability.** The safety counters live in Redis. If Redis is down,
  the safety-count read must not turn a healthy check into a 503. Mitigation: keep
  the count inside its own try/except (as today) and fall back to `0` on error —
  the existing Redis *dependency* probe already reports Redis health separately.
- **Redis client construction.** `core/config.py` exposes `redis_url`, not
  `redis_host`/`redis_port`, so the new `get_safety_monitor()` provider will use
  `redis.from_url(settings.redis_url)`. (The health probe block's use of
  `redis_host` is a separate pre-existing bug — out of scope here.)
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