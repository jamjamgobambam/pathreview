## Solution plan

**Issue:** Add a safety event count to the health check endpoint
https://github.com/ascherj/pathreview/issues/68 

## Understand
Root cause: /health never actually queried safety event data — safety_events_last_hour was a hardcoded placeholder (0), and even if it had called into SafetyMonitor, that class had no concept of a time window. It stored one counter per event type whose 24h TTL reset on every increment, so it could only ever produce an unbounded rolling total, not "events in the last hour."
Expected behavior: /health returns an accurate count of safety events (summed across all types) that occurred in the last hour, so operators can spot elevated safety activity from the health endpoint alone.
Actual behavior (before fix): Always returns 0, regardless of real activity.

## Map
safety/monitoring.py — SafetyMonitor class, specifically log_event(), get_event_count(); needed a new get_total_event_count().
api/routes/health.py — health_check(); needed to instantiate SafetyMonitor and populate the field from real data instead of a literal.
(Open item) — confirm actual import path for SafetyMonitor in the real codebase, since safety/monitoring.py was an assumption.

## Plan
Rework SafetyMonitor.log_event() to write to hourly-bucketed Redis keys (safety:events:{event_type}:{YYYYMMDDHH}) instead of a single key with a resetting TTL.
Rewrite get_event_count(event_type, window_hours) to sum the hourly buckets covering the requested window, rather than reading one unscoped key.
Add get_total_event_count(window_hours) to sum counts across all VALID_EVENT_TYPES into one aggregate number.
In health.py, keep the Redis client already created for the Redis dependency check accessible, instantiate SafetyMonitor(redis_client), and set safety_events_last_hour = safety_monitor.get_total_event_count(window_hours=1).
Fix the SafetyMonitor import path once the real module location is confirmed, and re-verify against a live Redis instance rather than stubs.

## Inputs & outputs
Input: the Redis client already live from the health check's Redis ping, current UTC time (internal), window_hours (defaults to 1).
Output: an integer written to health_status["safety_events_last_hour"] in the /health JSON response, or None if Redis is unreachable (so "zero events" and "couldn't check" aren't conflated).

## Risks & unknowns
Bucketing relies on datetime.utcnow(); clock skew across instances could cause inconsistent hour-boundary behavior.
get_total_event_count does up to 5 Redis GETs per health check (one per event type); fine for window_hours=1, but larger windows add more calls and latency.
Old-style keys from before this change (no hour suffix) won't be read by the new logic — a short gap in historical visibility right after deploy, though not a regression since the old scheme wasn't windowed either.
Only verified with stubbed redis/structlog in this environment (no network access to install real packages) — needs a real integration test before merging.
Still unsure whether operators want just the 1-hour aggregate, or also a per-event-type breakdown / additional windows (e.g., 24h) in the same response.

## Edge cases
Redis unreachable → safety_events_last_hour set to None, not a misleading 0.
Unknown/invalid event_type passed to log_event() → already logged as a warning and skipped, doesn't pollute the count.
No events in the window → clean 0 (missing Redis keys return None, treated as 0).
Window spanning a day boundary (e.g., checked at 00:30) → bucket keys roll over correctly via strftime.
Concurrent log_event() calls under load → Redis INCR is atomic per key, so no lost increments.