# PLAN.md

## Solution plan

**Issue:** Add a safety event count to the health check endpoint #68
<https://github.com/ascherj/pathreview/issues/68>

### Understand
The `/health` endpoint returns a `safety_events_last_hour` field but always sets it to `0` (`api/routes/health.py:78`). It never calls `safety.monitoring.SafetyMonitor`, which already stores per-event-type counts in Redis under keys `safety:events:<event_type>` and exposes them via `SafetyMonitor.get_event_count`. Expected: the field reflects real safety activity from the last hour so operators can monitor it without the monitoring dashboard. Actual: the field is a constant `0`.

### Map
Files involved:
- `api/routes/health.py` - `health_check()` builds the response; the safety-events block hardcodes `0`. Will wire it to `SafetyMonitor`.
- `safety/monitoring.py` - `SafetyMonitor.get_event_count(event_type, window_hours)` reads a single event type from Redis. No method sums across all event types; either add one or iterate `VALID_EVENT_TYPES`.
- `core/config.py` - `settings.redis_url` exists but `health.py` references `settings.redis_host`/`settings.redis_port` which are undefined on `Settings` (latent bug in the Redis block, AttributeError is swallowed). The fix will construct the Redis client / SafetyMonitor from `settings.redis_url` instead.
- `tests/unit/test_health.py` - new file with the failing repro test; will be expanded to assert correct behavior once fixed.

### Plan
1. Add a helper to `SafetyMonitor` (e.g. `get_total_event_count(window_hours=1)`) that sums `get_event_count` over all `VALID_EVENT_TYPES`, returning `0` on Redis errors. Keeps the existing single-type method intact.
2. In `health_check`, build a Redis client and `SafetyMonitor` from `settings.redis_url` and call the helper to populate `safety_events_last_hour`. Fall back to `0` and log on failure so health stays robust when Redis is down.
3. Update the repro test from a failing assertion to a passing one: patch `SafetyMonitor.get_total_event_count` (or the equivalent) to return `7` and assert the endpoint surfaces it; add a test for the Redis-down fallback returning `0` without breaking the endpoint.
4. Run `make test-unit`, `make lint`, `make typecheck`; fix any failures.

### Inputs & outputs
- Input: none from the caller (GET `/health`). Internally reads Redis safety event counters via `SafetyMonitor`.
- Output: `safety_events_last_hour` (int) in the 200/503 JSON body reflects the count of safety events logged in the last hour. Failures degrade to `0` with a logged warning rather than a crashed endpoint.

### Risks & unknowns
- `get_event_count` does not enforce the time window (per its own docstring); counts use Redis keys with a 24h TTL, so "last hour" is approximate until the monitor uses time-bucketed keys. Plan documents this and uses the existing method as-is; true windowed counts are out of scope for #68.
- Redis may be down. The fix must not make `/health` report unhealthy solely because safety counts are unavailable; keep current dependency semantics and only degrade the safety field.
- `settings.redis_host`/`redis_port` do not exist on `Settings`; using `redis_url` avoids that latent bug but changes how the Redis client is constructed inside `health_check`.

### Edge cases
- Redis unavailable or returns non-integer: return `0`, log, never raise from the safety block.
- No events of any type (keys absent): `get_event_count` already returns `0`; total is `0`.
- Unknown event types: `VALID_EVENT_TYPES` bounds the iteration; unknown types are ignored by `log_event`.
- Endpoint returns 503 when dependencies are down: the safety field must still be present in the `detail` payload.