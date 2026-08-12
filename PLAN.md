# PLAN — Issue #66: Safety monitoring doesn't emit windowed metrics across multi-turn conversations

**Issue:** https://github.com/ascherj/pathreview/issues/66
**Branch:** `fix/66-safety-monitor-multi-turn-metrics`

## 1. Problem

`SafetyMonitor` ([safety/monitoring.py](safety/monitoring.py)) records safety
events (e.g. `content_filtered`, `injection_attempt`) so the system can react
when a user trips safety limits repeatedly. In a multi-turn conversation a user
can bypass the per-message content filter by spreading a harmful request across
several turns — each message looks benign on its own, but the pattern across a
short window is not.

Detecting that pattern requires asking *"how many safety events occurred in the
last N hours?"*. The current code cannot answer that question:

1. **No per-event timestamps.** `log_event` stores a single cumulative counter
   (`INCR safety:events:{type}`) with a key-level 24h expiry. There is no record
   of *when* each event happened.
2. **`window_hours` is a no-op.** `get_event_count(event_type, window_hours=1)`
   accepts the argument but ignores it (docstring: *"not enforced here"*) and
   returns the lifetime total via a single `GET`.

Result: a 1-hour window and a 1000-hour window return the same number, so a
multi-turn bypass is never reflected in a time-windowed metric.

## 2. Reproduction

Test: [tests/unit/test_monitoring.py](tests/unit/test_monitoring.py) ::
`test_window_hours_is_ignored_reproduces_66`.

It records that 5 events exist all-time but only 2 within the last hour, then
calls `get_event_count("content_filtered", window_hours=1)` and asserts the
result is `2`. Against the current implementation it returns `5` and the test
fails — that failure is the reproduction.

```
AssertionError: window_hours ignored: got 5 (all-time total) instead of 2 ...
assert 5 == 2
```

## 3. Proposed fix

Adopt the same rolling-window pattern already used by
[safety/rate_limiter.py](safety/rate_limiter.py), which stores timestamped
entries in a Redis **sorted set** (`ZADD` / `ZREMRANGEBYSCORE` / `ZCARD`).

### 3.1 `log_event` — store timestamped events
- Continue validating `event_type` against `VALID_EVENT_TYPES`.
- Instead of (or in addition to) `INCR`, add the event to a sorted set keyed by
  event type, scored by the current UNIX timestamp:
  `ZADD safety:events:{event_type} {now: now}`.
- Set a key expiry generous enough to cover the largest window we query
  (e.g. 24h), so the set self-trims.
- Keep the existing structlog line and the broad `try/except` so logging failures
  never break the request path.

### 3.2 `get_event_count` — enforce the window
- Compute `window_start = now - window_hours * 3600`.
- Trim expired entries: `ZREMRANGEBYSCORE key 0 window_start`.
- Return the count inside the window: `ZCARD key`.
- Preserve the existing behaviour on error (log + return `0`).

### 3.3 (Optional, if in scope) surface the metric
Grep shows `SafetyMonitor` currently has no callers. If wiring is in scope, call
`log_event(...)` where the content filter / prompt-defense layers flag input, and
expose `get_event_count(..., window_hours=1)` so the agent can react (e.g. warn or
block) when the windowed count crosses a threshold. If out of scope for #66, note
it as follow-up.

## 4. Testing

- The reproduction test flips from failing to passing once `get_event_count`
  reads the windowed sorted-set count.
- Add coverage for:
  - `log_event` calls `zadd` with a timestamp score and sets an expiry.
  - `log_event` still rejects unknown event types (already covered).
  - `get_event_count` calls `zremrangebyscore` with the correct `window_start`
    and returns `zcard`.
  - Error path returns `0`.
- Run: `make test-unit` (or `.venv/bin/pytest tests/unit/test_monitoring.py -v`).

## 5. Risks / considerations

- **Data-model change:** counts recorded under the old `INCR` key won't carry
  over. Acceptable — safety metrics are ephemeral (24h expiry) and dev-only.
- **Memory:** a sorted set is larger than one integer, but bounded by the expiry
  window and event volume; the rate limiter already accepts this trade-off.
- **Clock source:** use a single `now` per call, mirroring `rate_limiter.py`.

## 6. Out of scope

- Redesigning the content filter's detection patterns.
- Persisting safety events beyond the rolling window (no long-term audit store).
