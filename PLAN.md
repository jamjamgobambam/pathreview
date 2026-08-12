## Solution plan

**Issue:** #68 — `/health` always reports `safety_events_last_hour` as a hardcoded `0`

### Understand

`GET /health` declares a `safety_events_last_hour` field in its response, but the
old implementation just assigned it the literal `0` — it never read from anywhere.
Operators had no way to see safety system activity (PII redactions, blocked
injection attempts, rate limiting, etc.) without going to the monitoring dashboard
directly.

Expected: the field reflects a real, rolling one-hour count of safety events.
Actual (confirmed via reproduction in `JOURNAL.md`): always `0`, regardless of how
many safety events had occurred.

Digging in, this wasn't a one-line wiring fix — three things blocked it:

1. `SafetyMonitor` (`safety/monitoring.py`) was fully defined but never
   instantiated anywhere in the app.
2. No shared Redis client existed. The only Redis usage was an ad hoc client in
   `health.py`'s own dependency check, built from `settings.redis_host` /
   `settings.redis_port` — fields that don't exist on `Settings` (only
   `redis_url` does). That call raised `AttributeError` on every request, silently
   caught and reported as `redis: "unhealthy"` even when Redis was fine.
3. `get_event_count(event_type, window_hours)` didn't enforce `window_hours` at
   all — it read a flat `INCR` counter with a fixed 24h TTL, so the parameter was
   accepted but ignored (confirmed by reproduction: a near-zero window and a 24h
   window returned the identical count).

### Map

Files touched:

- `api/routes/health.py` — wire in the real safety count, fix the Redis dependency
  check, fix `db.execute()` (was passed a raw string instead of `sqlalchemy.text()`).
- `core/redis.py` (new) — shared `get_redis()` FastAPI dependency.
- `safety/monitoring.py` — rework `log_event` / `get_event_count` to actually
  enforce a rolling window; add `get_total_event_count`.
- `pyproject.toml` — whitelist `fastapi.Depends` for ruff's B008 check (false
  positive for FastAPI's DI pattern once `Depends(get_redis)` is added).
- `tests/unit/test_health.py` (new), `tests/unit/test_monitoring.py` (new) —
  no prior coverage existed for either file.

### Plan

1. Add `core/redis.py` with a `get_redis()` dependency built from
   `settings.redis_url`, mirroring the existing `get_db()` pattern in
   `core/database.py`. This becomes the single Redis connection point for the
   route instead of two ad hoc clients.
2. Rework `SafetyMonitor.log_event` to record events in a Redis sorted set
   (`ZADD safety:events:{event_type} {ts} {ts}:...`) scored by timestamp, with a
   25h `EXPIRE` for cleanup of fully idle keys.
3. Rework `get_event_count` to actually enforce `window_hours`: trim stale
   entries with `ZREMRANGEBYSCORE` then count the remaining window with
   `ZCOUNT`. Add `get_total_event_count(window_hours)` summing across
   `VALID_EVENT_TYPES` — that's the single aggregate number `/health` needs.
4. Wire `Depends(get_redis)` into `health_check`, instantiate `SafetyMonitor`,
   populate `safety_events_last_hour` from `get_total_event_count(window_hours=1)`,
   and replace the old ad hoc Redis client in the dependency-check block with the
   shared client. Fix `db.execute("SELECT 1")` → `db.execute(text("SELECT 1"))`
   while adding type annotations (this bug only surfaced once annotating the
   function forced the mismatch to be visible).
5. Add regression tests: `test_monitoring.py` covers window eviction/inclusion
   and total-count summation; `test_health.py` covers the happy path, a redis
   failure during the safety-count lookup degrading to `0` (not a 503), and
   redis/postgres-down still returning 503.

### Inputs & outputs

- **Input:** a shared Redis client (via DI), events written by `SafetyMonitor.log_event`
  calls elsewhere in the codebase, and the incoming `GET /health` request.
- **Output:** the `/health` JSON payload's `safety_events_last_hour` becomes a real
  windowed count instead of a constant; `dependencies.redis` reflects actual Redis
  reachability instead of always failing; `dependencies.postgres` check no longer
  risks passing a raw string where the driver expects a `TextClause`.

### Risks & unknowns

- **Redis key growth:** sorted sets are bounded by TTL + trim-on-read, so idle keys
  expire and active keys stay small. No unbounded growth expected.
- **Clock source:** used `time.time()` consistently for scores between writer and
  reader to avoid timezone/format drift.
- **Backward compatibility of `get_event_count`:** changing its semantics in place
  (rather than adding a new method) is only safe because nothing else in the
  codebase calls it yet — confirmed via search before changing behavior.
- **Failure isolation:** a safety-count lookup failure must not flip the overall
  `/health` status to `"unhealthy"` — a monitoring-query hiccup shouldn't page
  anyone. Decided to catch and degrade to `0`, consistent with how `vector_db`
  unavailability reports `"unavailable"` rather than failing the whole check.

### Edge cases

- No events logged for a given event type → `zcount` returns `0`, sums to `0`,
  no exception.
- Redis reachable but the safety-count query itself fails → caught, logged,
  `safety_events_last_hour` defaults to `0`, endpoint still returns `200`.
- Redis unreachable entirely (`ping` fails) → overall `status: "unhealthy"`,
  `503`, independent of the safety count path.
- Unknown `event_type` passed to `log_event` → already rejected with a warning
  log, nothing written to Redis.
- Fractional/very small `window_hours` → supported now that the type changed
  from `int` to `float`.
