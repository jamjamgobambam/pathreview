# Issue #68 Solution Plan

## Issue

- **Link:** https://github.com/ascherj/pathreview/issues/68
- **Title:** Add a safety event count to the health check endpoint
- **Tier:** Tier 1

## Problem

The `/health` endpoint exposes a `safety_events_last_hour` field, but the value is a
hard-coded placeholder. `SafetyMonitor` records safety activity in Redis, yet the health
route never reads those records. Operators therefore see zero safety events even after the
application detects PII, prompt injection, filtered content, bias, or rate limiting.

## Reproduction

With the local Redis and API services running:

1. Read the current `pii_detected` count through `SafetyMonitor`.
2. Call `SafetyMonitor.log_event("pii_detected", ...)`.
3. Confirm the stored count increases.
4. Request `GET /health`.

Observed on July 24, 2026:

```text
Redis before event: 0
Redis after event:  1
/health safety_events_last_hour: 0
```

The endpoint also reported PostgreSQL and Redis as unhealthy because of separate known
issues #154 and #155. Those dependency statuses do not affect this reproduction: the
safety event was successfully stored in Redis while the response still reported zero.

## Expected Behavior

`safety_events_last_hour` should equal the total number of valid safety events recorded
during the rolling one-hour window. Events older than one hour, invalid event types, and
failed writes must not increase the count.

## Root Cause

`api/routes/health.py` explicitly assigns `0` instead of querying `SafetyMonitor`.
Additionally, `SafetyMonitor` uses integer counters with a 24-hour expiry. Those counters
do not preserve event timestamps, so they cannot accurately calculate a rolling one-hour
metric.

## Proposed Solution

Store safety events in one Redis sorted set per event type:

- Use the event timestamp as the sorted-set score.
- Use a timestamp plus UUID as the member so simultaneous events remain distinct.
- Use a new `safety:events:timeline:*` namespace so old integer counter keys cannot cause
  Redis type conflicts during deployment.
- Give each key a 24-hour retention period for cleanup and possible future metrics.
- Before counting, remove scores at or before the requested window cutoff.
- Count the remaining scores inside the rolling window.
- Add an aggregate method that sums all valid safety event types.
- Have `/health` construct a monitor from `settings.redis_url` and populate the response
  from the aggregate one-hour count.
- Fail safely: if safety metric retrieval fails, log the error and retain the default zero
  without crashing the health endpoint.

## Files to Change

- `safety/monitoring.py`
  - Replace non-time-aware counters with sorted-set event storage.
  - Enforce the requested rolling window.
  - Add an aggregate count across valid event types.
- `api/routes/health.py`
  - Replace the placeholder with the real aggregate count.
- `tests/unit/test_safety_monitoring.py`
  - Cover event storage, windows, aggregation, invalid types, and Redis failures.
- `tests/unit/test_health.py`
  - Verify the endpoint uses the real safety count and handles metric failures.

## Test Plan

1. No recorded events returns `0`.
2. A recent valid event is stored with a timestamp and expiration.
3. Multiple recent events are counted.
4. A custom rolling window is converted to the correct cutoff.
5. Events at or older than the one-hour cutoff are removed and excluded.
6. Counts from all valid event types are aggregated.
7. An invalid event type is ignored.
8. A Redis write failure is logged without raising.
9. A Redis read failure returns `0` without raising.
10. `/health` reports the monitor's real aggregate count.
11. `/health` retains zero if safety metric retrieval fails.
12. Run the focused tests, full unit suite, linter, formatter check, and type checker.

## Risks and Mitigations

- **Duplicate timestamps:** append a UUID to every sorted-set member.
- **Legacy counter type conflicts:** use a new timeline key namespace rather than reusing
  existing integer counter keys.
- **Unbounded Redis growth:** expire keys after 24 hours and prune old scores while
  reading.
- **Boundary ambiguity:** treat events at or before the cutoff as expired.
- **Monitoring outage:** fail safely to zero and emit a structured error log.
- **Scope overlap with health issues #154/#155:** do not change the existing PostgreSQL or
  Redis dependency probes as part of #68.

## Implementation Steps

1. Add timestamped sorted-set storage to `SafetyMonitor.log_event`.
2. Make `get_event_count` enforce the requested rolling window.
3. Add `get_total_event_count`.
4. Connect `/health` to the aggregate count through `settings.redis_url`.
5. Add focused unit tests for the monitor and route.
6. Run all checks and review the final diff against `CONTRIBUTING.md`.
