# Journal

## Issue #68 — `/health` always reports `safety_events_last_hour: 0`

**Branch:** `fix/68-safety-event-count-health-check`

### Reproduction steps

Checked out the pre-fix state of the two relevant files (parent commit `d5f196d`,
before the fix in `c1aa518`) and exercised them directly — no live Postgres/Redis/
Docker required, using a minimal in-memory stand-in for `redis.Redis`:

```
git show d5f196d:safety/monitoring.py > old_monitoring.py
git show d5f196d:api/routes/health.py  > old_health.py
```

Then logged 5 `pii_detected` events through the old `SafetyMonitor` and called
`get_event_count()` with both a near-zero window and a 24h window.

### Confirmed bugs

1. **`get_event_count(event_type, window_hours)` ignores `window_hours` entirely.**
   Old implementation was `self.redis.get(key)` against a flat `INCR` counter with a
   fixed 24h TTL — the parameter was accepted but never used (its own docstring even
   said "not enforced here; for reference"). Reproduced: after logging 5 events,
   `get_event_count(window_hours=0.0000001)` returned `5`, identical to
   `get_event_count(window_hours=24)` — a window that should have excluded
   everything returned the same count as a 24-hour window.

2. **`health_check()` hardcodes `safety_events_last_hour` to the literal `0`.**
   `SafetyMonitor` was never imported or instantiated in `api/routes/health.py`, so
   the field could never reflect real activity regardless of how many safety events
   occurred.

3. **The ad hoc Redis client in the old health dependency check reads
   `settings.redis_host` / `settings.redis_port`, which don't exist on `Settings`**
   (`core/config.py` only ever defined `redis_url`). Reproduced:
   `hasattr(Settings(), "redis_host")` and `hasattr(Settings(), "redis_port")` are
   both `False`. That means the old `redis.Redis(host=..., port=...)` call raised
   `AttributeError` on every single request, silently caught by the bare
   `except Exception`, so `/health` always reported `redis: "unhealthy"` even when
   Redis was actually up and reachable.

### Status

Fixed in `c1aa518` (`fix(api): surface safety event counts in /health`), same
branch: added a shared `core.redis.get_redis()` dependency using `settings.redis_url`,
reworked `SafetyMonitor` to use a Redis sorted set so `window_hours` is actually
enforced, and wired `SafetyMonitor` into `/health`. See
`docs/plans/safety-events-health-metric.md` for the full design writeup, and
`tests/unit/test_health.py` / `tests/unit/test_monitoring.py` for regression coverage
added alongside the fix.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Qianyu2021/pathreview/commit/5e1950f

**Reproduction summary:**
Checked out the pre-fix version of `api/routes/health.py` and `safety/monitoring.py`
(parent commit `d5f196d`) and ran them directly: logging 5 events and calling
`get_event_count()` with a near-zero window vs. a 24h window both returned `5`,
confirming `window_hours` was never enforced, and confirmed `health_check()` hardcoded
`safety_events_last_hour` to `0` regardless of any logged events.

**PLAN.md link:** https://github.com/Qianyu2021/pathreview/blob/fix/68-safety-event-count-health-check/PLAN.md
