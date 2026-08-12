# Plan: Surface safety event activity in /health

## Problem

`GET /health` ([api/routes/health.py](../../api/routes/health.py)) already declares a
`safety_events_last_hour` field in its response, but it's a hardcoded placeholder:

```python
health_status["safety_events_last_hour"] = 0
```

Operators can't see safety system activity (PII redactions, blocked injections, rate
limiting, etc.) without going to the monitoring dashboard directly. We need this field
to reflect real counts.

## Root cause / why this isn't a one-line wiring fix

`SafetyMonitor` ([safety/monitoring.py](../../safety/monitoring.py)) is fully defined but
**never instantiated anywhere in the app** — not in health.py, not in any middleware.
Two things block a naive "just call it from health.py":

1. **No shared Redis client exists.** The only Redis usage today is the ad hoc client in
   `health.py`'s own dependency check:
   ```python
   r = redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)
   ```
   `settings.redis_host` / `settings.redis_port` don't exist on `Settings`
   ([core/config.py](../../core/config.py) only defines `redis_url`) — this call raises
   `AttributeError` today, which is silently caught and reported as `"unhealthy"`. This is
   a pre-existing latent bug we need to fix anyway since we're adding a second Redis
   consumer to this file.

2. **`get_event_count` doesn't actually implement a time window.** `log_event` stores a
   flat per-event-type counter (`INCR safety:events:{event_type}`) with a fixed 24h TTL
   reset only when the key is first created. `get_event_count(event_type, window_hours)`
   accepts `window_hours` but its own docstring says *"not enforced here; for reference"*
   — it just returns whatever the flat counter holds, which could represent anywhere from
   seconds to 24 hours of accumulation. Calling this as-is and labeling the result
   `safety_events_last_hour` would be misleading to operators (the name promises a 1-hour
   window; the data could be a 24-hour total). Since nothing in the codebase calls
   `get_event_count` today (confirmed via search), we're free to fix its semantics
   directly rather than bolt on a parallel method.

So the real fix has three parts: a shared Redis dependency, a real sliding-window counter
in `SafetyMonitor`, and the health.py wiring.

## Proposed approach

### 1. Shared Redis dependency (`core/redis.py`, new file)

Add a `get_redis()` FastAPI dependency mirroring the existing `get_db()` pattern in
[core/database.py](../../core/database.py):

```python
import redis
from core.config import settings

_redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

def get_redis() -> redis.Redis:
    return _redis_client
```

Use `settings.redis_url` (already defined) instead of the nonexistent `redis_host`/
`redis_port`, fixing the latent bug as a side effect. This client is reused by both the
existing dependency health check and the new safety-monitor lookup, so we don't open two
separate connections per request.

### 2. Real sliding-window counting (`safety/monitoring.py`)

Replace the flat `INCR` counter with a Redis sorted set per event type, scored by event
timestamp:

- `log_event`: `ZADD safety:events:{event_type} {ts} {ts}:{uuid4()}` (unique member per
  event so simultaneous events aren't collapsed), plus `EXPIRE` on the key for cleanup of
  fully idle keys (e.g. 25h, comfortably above the largest window we query).
- `get_event_count(event_type, window_hours=1)`:
  - `ZREMRANGEBYSCORE key -inf (now - window)` to evict stale entries.
  - `ZCOUNT key (now - window) +inf` to get the real windowed count.
  - This makes the existing `window_hours` parameter actually do what its name says.
- New `get_total_event_count(window_hours=1) -> int`: sums `get_event_count` across all
  `VALID_EVENT_TYPES`. This is what health.py will call — operators want one aggregate
  number in the health payload, not a breakdown (no existing consumer needs per-type
  breakdown; confirmed via search).

Sorted sets are the right structure here over time-bucketed keys: eviction and counting
are both native single Redis calls, and event volume for a safety monitor is low enough
that per-event members are cheap.

### 3. Wire into health.py

- Add `Depends(get_redis)` alongside the existing `Depends(get_db)`.
- Instantiate `SafetyMonitor(redis_client)` and call
  `monitor.get_total_event_count(window_hours=1)`.
- Replace the ad hoc `redis.Redis(host=..., port=...)` block in the dependency-check
  section with the shared client from `get_redis()`, so there's one Redis connection
  point in this file, not two.
- Failure handling: if the safety count lookup raises, log the error and leave
  `safety_events_last_hour` at `0` — a monitoring-query failure must not flip overall
  `status` to `"unhealthy"` (same treatment as the current placeholder's bare `try/except`,
  and consistent with how `vector_db` unavailability is reported as `"unavailable"` rather
  than failing the whole check).

## Files touched

| File | Change |
|---|---|
| `core/redis.py` (new) | `get_redis()` dependency using `settings.redis_url` |
| `safety/monitoring.py` | Sorted-set backed `log_event` / `get_event_count`; new `get_total_event_count` |
| `api/routes/health.py` | Use `get_redis()` for the dependency check; instantiate `SafetyMonitor` and populate `safety_events_last_hour` from `get_total_event_count(window_hours=1)` |

## Testing plan

No tests currently exist for either file (confirmed via search) — this is a good time to
add coverage for both:

- `tests/unit/test_monitoring.py` (new): use `fakeredis` (already a pattern-compatible
  choice given `tests/unit/test_rate_limiter.py` mocks a redis client for
  `RateLimiter`) to verify:
  - events older than the window are excluded from `get_event_count`.
  - events within the window are included.
  - `get_total_event_count` sums correctly across multiple event types.
  - unknown event types are rejected without raising (existing behavior, keep covered).
- `tests/unit/test_health.py` (new): use FastAPI `TestClient` with a fake/mock redis
  dependency override to assert:
  - `safety_events_last_hour` reflects events logged via `SafetyMonitor` in the test.
  - a redis failure during the safety-count lookup degrades to `0` without a 503.

## Risks / open questions

- **Redis key growth**: sorted sets are bounded by TTL + trim-on-read, so idle keys expire
  and active keys stay small (trimmed to the query window on every read). No unbounded
  growth expected.
- **Clock source**: use `datetime.utcnow().timestamp()` consistently for scores (matching
  existing `datetime.utcnow()` usage elsewhere in this file) to avoid timezone drift
  between writer and reader.
- **Naming**: confirmed no external caller depends on the current `get_event_count`
  signature/semantics, so changing its behavior in place (rather than adding a new
  method) is safe.
