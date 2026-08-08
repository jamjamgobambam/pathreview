## Solution plan

**Issue:** [#68 — Add a safety event count to the health check endpoint](https://github.com/ascherj/pathreview/issues/68)

### Understand

**Expected behavior:** `GET /health` returns a `safety_events_last_hour` field
that reflects real safety-system activity (PII detections, prompt injection
attempts, content filtering, bias flags, rate limiting) so an operator can
tell from the health endpoint alone whether the safety system is seeing
traffic, without checking a separate dashboard.

**Actual behavior:** `health_check` (`api/routes/health.py:75-80`) hardcodes
`safety_events_last_hour` to `0` inside a try/except that does nothing else.
The comment above it literally says "This would be populated by actual
safety event logging" — it never was. The field is always `0` regardless of
what's happened in Redis.

**Root cause:** The health route was never wired up to `SafetyMonitor`
(`safety/monitoring.py`), even though `SafetyMonitor.get_event_count(event_type)`
already exists and reads real per-event-type counters from Redis
(key pattern `safety:events:<event_type>`, incremented by
`SafetyMonitor.log_event`). The route just never instantiates or calls it.

**Confirmed via reproduction:** `tests/unit/test_health_safety_events.py`
mocks Redis to report 1 recorded `pii_detected` event and asserts
`health_check` surfaces it. It fails today with `assert 0 == 1`, with
postgres/redis/vector_db all reporting healthy — isolating the failure to
exactly this hardcoded field.

**Related but out-of-scope finding:** `core/config.py`'s `Settings` class
only defines `redis_url`, not `redis_host`/`redis_port`, but
`health.py:44-46` reads `settings.redis_host` / `settings.redis_port` when
constructing the Redis health-check client. That raises `AttributeError`
every time, silently swallowed by the surrounding `except Exception`, so the
Redis dependency check in `/health` always reports "unhealthy" in practice.
This is a real bug but a separate one from #68 (it affects the `dependencies.redis`
field, not `safety_events_last_hour`) — noting it here so it isn't confused
with this fix, and flagging it as a candidate follow-up issue.

### Map

Files expected to be touched:

- **`api/routes/health.py`** — primary fix. Replace the hardcoded `0` block
  (lines 75-80) with a call into `SafetyMonitor`, summed across
  `SafetyMonitor.VALID_EVENT_TYPES`, wrapped so a Redis outage degrades
  gracefully instead of taking down `/health`.
- **`safety/monitoring.py`** — no behavior change expected, but I need a
  helper here (or in the route) to sum counts across all valid event types,
  since `get_event_count` only returns one event type at a time. Likely add
  a small `get_total_event_count()` method to `SafetyMonitor` rather than
  looping in the route, to keep the aggregation logic testable alongside the
  rest of the class.
- **`core/database.py`** / **`core/config.py`** — read-only, to confirm how
  the existing `get_db` dependency and Redis connection settings are meant
  to be constructed, so the health route's Redis client construction is
  consistent with how the rest of the app builds one (may reveal whether the
  `redis_host`/`redis_port` bug above should be fixed as part of getting a
  working Redis client for the safety count, since I need a working Redis
  connection either way).
- **`tests/unit/test_health_safety_events.py`** — reproduction test now;
  will extend with passing cases (zero events, multiple event types, Redis
  unavailable) once the fix lands.

### Plan

1. **Add an aggregation method to `SafetyMonitor`.** Add
   `get_total_event_count(window_hours: int = 1) -> int` to
   `safety/monitoring.py` that sums `get_event_count(event_type)` over
   `VALID_EVENT_TYPES`, catching Redis errors the same way `get_event_count`
   already does (log and return partial/zero rather than raising).
2. **Wire the health route to a real Redis client + `SafetyMonitor`.**
   In `api/routes/health.py`, construct (or reuse) a `redis.Redis` client —
   this is also where I decide whether to fix the `redis_host`/`redis_port`
   vs `redis_url` mismatch as a prerequisite, since the safety count needs a
   working Redis connection to mean anything — and instantiate
   `SafetyMonitor(redis_client)`.
3. **Replace the hardcoded placeholder.** Swap
   `health_status["safety_events_last_hour"] = 0` for
   `safety_monitor.get_total_event_count()`, inside a try/except so a Redis
   failure sets the count to `0` (or `null`) and logs, without flipping
   `health_status["status"]` to `"unhealthy"` — a quiet safety subsystem
   isn't itself a health-check failure the way a down Postgres is.
4. **Update `tests/unit/test_health_safety_events.py` into a full suite.**
   Turn today's single failing reproduction case into passing coverage:
   zero events, single event type, multiple event types summed, and a
   Redis-unavailable case that should return `0`/`null` without raising or
   marking the app unhealthy.
5. **Manually verify against a live stack.** Run the app locally (per
   `docs/SETUP.md`), trigger a safety event through the existing
   `pii_scrubber`/`prompt_defense`/`bias_detector` paths (whichever already
   call `SafetyMonitor.log_event`), and confirm `curl localhost:<port>/health`
   reflects a non-zero count.

### Inputs & outputs

- **Input:** an HTTP `GET /health` request; implicitly, whatever safety
  events have been logged to Redis via `SafetyMonitor.log_event` in the
  preceding window (via the `safety:events:<event_type>` keys' TTLs).
- **Output:** the existing JSON health payload, unchanged in shape, except
  `safety_events_last_hour` now contains a real integer sum instead of a
  hardcoded `0`. No new fields, no schema change — this is a semantic fix,
  not a new endpoint.

### Risks & unknowns

- **The "last hour" window isn't actually enforced.** `SafetyMonitor.log_event`
  sets a flat 24-hour TTL on each counter key and `get_event_count`'s
  `window_hours` parameter is documented as "not enforced here; for
  reference" (`safety/monitoring.py:61`). So a naive fix will report
  "events in the last 24 hours," not "last hour," despite the field name.
  Need to decide: rename semantics honestly, or actually bucket by hour
  (e.g. a key per hour, like `safety:events:<type>:<hour-bucket>`), which is
  a bigger change than the issue implies. Leaning toward proposing the
  honest-renaming path first and flagging the windowing gap explicitly,
  since reworking the storage scheme touches `log_event` too and risks
  breaking whatever (if anything) else reads these Redis keys.
- **The `redis_host`/`redis_port` vs `redis_url` mismatch** (see Understand)
  means I can't just reuse `health.py`'s existing Redis-construction code
  as-is for the safety client — I either fix that bug as a prerequisite or
  build a separate, correctly-configured Redis client just for
  `SafetyMonitor`, which would leave the pre-existing bug in place. Need to
  confirm with a mentor/issue tracker whether fixing it in-scope here is
  welcome or should be its own PR.
- **No existing test coverage for `health.py` or `safety/monitoring.py`'s
  Redis interaction** beyond what I just added — I don't yet know if
  `tests/integration/` (currently empty except `__init__.py`) is meant to
  hold a real end-to-end health check against Dockerized Redis, or if unit
  tests with mocked Redis are considered sufficient for this repo.
- **Concurrency/staleness:** Redis errors during the safety count should not
  flip the overall `/health` status to unhealthy (a transient safety-metrics
  blip shouldn't page anyone the way a down Postgres should), but I need to
  confirm that's the right call rather than assuming it.

### Edge cases

- Redis is unreachable when `/health` is called → count should degrade to
  `0` (or an explicit `null`/`"unavailable"` sentinel — TBD) without raising
  and without marking `/health` overall `"unhealthy"`.
- No safety events have ever fired → count is `0` (already the default
  behavior; should stay `0`, not error).
- Only some event types have fired (e.g. `pii_detected` but not
  `bias_detected`) → sum should still be correct; `get_event_count` already
  returns `0` for a key that doesn't exist, so this should fall out of the
  aggregation naturally, but needs a test to confirm.
- A key exists in Redis for an event type outside `VALID_EVENT_TYPES`
  (shouldn't happen since `log_event` rejects unknown types, but defensive
  aggregation should only iterate `VALID_EVENT_TYPES`, not scan Redis keys
  by pattern, to avoid counting garbage).
- High event volume / large counts → `int(count)` conversion in
  `get_event_count` should handle normal integer ranges fine; no special
  handling anticipated, but worth a quick sanity check with a large mocked
  value.

### Resolution

Implemented as described in Plan steps 1–3, with these calls made on the
open risks/unknowns above:

- **`redis_host`/`redis_port` bug:** left as a separate, pre-existing bug.
  The safety-events block builds its own client via
  `redis.Redis.from_url(settings.redis_url, ...)`, independent of the
  broken `redis_host`/`redis_port` construction in the dependency check
  above it, so the fix doesn't need that bug fixed as a prerequisite.
- **"Last hour" windowing:** kept the honest-comment path, not a storage
  rework. `get_total_event_count`'s docstring and the call site in
  `health.py` both note that counts reflect `SafetyMonitor`'s flat 24-hour
  TTL, not a true rolling hour — reworking the Redis key scheme to bucket
  by hour would touch `log_event` and is flagged as a follow-up, not done
  here.
- **Redis failure handling:** confirmed via the edge-case tests — a Redis
  error while counting safety events degrades `safety_events_last_hour` to
  `0` and does not flip `health_status["status"]` to `"unhealthy"`.
- **Test coverage:** added unit tests only (`tests/unit/test_health_safety_events.py`,
  `tests/unit/test_safety_monitoring.py`), with mocked Redis. Did not add
  anything under `tests/integration/` — no existing pattern there to match
  and out of scope for this fix.
