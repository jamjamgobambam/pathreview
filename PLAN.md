# Solution plan

**Issue:** D-08 — "Add a safety event count to the health check endpoint"
(from `scripts/issues_manifest.json`; seeded into the PathReview issue tracker)

### Understand

**Root cause.** The `/health` endpoint already exposes a `safety_events_last_hour`
field in its response, but [`api/routes/health.py`](api/routes/health.py) hardcodes
it to `0`:

```python
# Count safety events in last hour (placeholder)
try:
    # This would be populated by actual safety event logging
    health_status["safety_events_last_hour"] = 0
except Exception as exc:
    log.error("safety_events_check_failed", error=str(exc))
```

The data it should surface already exists: [`safety/monitoring.py`](safety/monitoring.py)
has `SafetyMonitor.get_event_count(event_type, window_hours=1)`, which reads
per-type counts from Redis (keys `safety:events:{event_type}`). The endpoint
simply never calls it — so operators always see `0` regardless of real activity.

**Expected vs. actual.**
- *Expected:* `safety_events_last_hour` reflects the number of safety events
  (PII detections, injection attempts, content filters, bias detections, rate
  limits) recorded in the recent window.
- *Actual:* it is always `0`. Reproduced by
  `tests/unit/test_health_safety_events.py::test_health_reports_recorded_safety_events`,
  which records 3 events through `SafetyMonitor` and asserts the endpoint
  reports them — it reports `0`, failing with
  `assert 0 == 3`.

**Secondary correctness gap.** `get_event_count`'s `window_hours` argument is
documented as *"not enforced here; for reference"* — it returns the cumulative
count under a 24h key expiry, not a true rolling one-hour count. A faithful
`safety_events_last_hour` needs real hourly windowing, so this is in scope to at
least decide on and document.

### Map

Files I expect to touch:

- [`api/routes/health.py`](api/routes/health.py) — replace the hardcoded `0`
  with a real count summed across `SafetyMonitor.VALID_EVENT_TYPES`, using a
  Redis client, degrading to `0` if Redis is unavailable.
- [`safety/monitoring.py`](safety/monitoring.py) — add a helper for the rolling
  one-hour total (e.g. `get_total_event_count(window_hours=1)`) and, if we do
  true windowing, switch `log_event`/`get_event_count` to hour-bucketed keys
  (`safety:events:{type}:{YYYYMMDDHH}`).
- [`tests/unit/test_health_safety_events.py`](tests/unit/test_health_safety_events.py)
  — flip the reproduction test to assert the correct count, and add cases for
  "no events" and "Redis unavailable".

Reference (context, likely not edited): [`core/config.py`](core/config.py) —
see the Redis-settings risk below; callers of `SafetyMonitor.log_event` in
`safety/` that establish which event types actually fire.

### Plan

1. **Expose a total-count helper.** Add `get_total_event_count(window_hours=1)`
   to `SafetyMonitor` that sums `get_event_count` across `VALID_EVENT_TYPES`,
   so the endpoint has one call to make.
2. **Wire it into `/health`.** In the safety block of `health_check`, build a
   `SafetyMonitor` from a Redis client and set
   `health_status["safety_events_last_hour"] = monitor.get_total_event_count()`.
   Keep the `try/except` so a Redis failure logs and leaves the value at `0`
   instead of 500-ing the health check.
3. **Make the window real (or explicitly deferred).** Decide between (a) true
   hour-bucketed keys summed over the last `window_hours`, or (b) documenting
   the current 24h-expiry cumulative behavior as a known limitation with a
   follow-up issue. Reflect the decision in the docstring and the PR.
4. **Update tests.** Turn the reproduction test green (endpoint reports the
   recorded count) and add: zero events → `0`; Redis raising → `0` (no crash).
5. **Verify.** `make check && make test-unit`, plus a manual `curl /health`
   showing a non-zero count after triggering a safety event.

### Inputs & outputs

- **Input:** a `GET /health` request; internally, per-type safety counts stored
  in Redis by `SafetyMonitor.log_event`.
- **Output / change:** the `safety_events_last_hour` field in the `/health`
  JSON now returns the summed recent safety-event count (integer ≥ 0) instead of
  a constant `0`. No change to the endpoint's status/HTTP-code logic.

### Risks & unknowns

- **Redis access in `health.py` is currently broken independently of D-08.** The
  endpoint reads `settings.redis_host` / `settings.redis_port`, but
  `core/config.py` only defines `redis_url` — so the Redis block already raises
  `AttributeError` and marks Redis unhealthy. My fix must obtain a working Redis
  client (parse `settings.redis_url`, or reuse a shared client) or the count
  will silently stay `0`. Flagging this as a real dependency, not a hypothetical.
- **Window semantics.** If I keep `get_event_count` as-is, "last hour" is a
  misnomer (it's really "last 24h, cumulative"). True windowing means changing
  the key scheme in `log_event`, which touches every event producer — larger
  blast radius. Need to decide scope with the maintainer.
- **Constructing a client per health call** adds a Redis round-trip to a
  hot endpoint; acceptable for `/health` but worth noting.
- **Which event types count.** Summing all `VALID_EVENT_TYPES` assumes each is
  equally a "safety event"; confirm `rate_limited` should be included.

### Edge cases

- No events recorded → `0` (and the sanity path must not error on missing keys).
- Redis unavailable / raising → field is `0`, `/health` still responds, error
  logged (no 500 from the safety block).
- Keys just expired at the hour boundary → count rolls off as designed.
- An event type in Redis that isn't in `VALID_EVENT_TYPES` → ignored (only known
  types are summed).
- Large counts → returned as a plain integer; no formatting assumptions.
