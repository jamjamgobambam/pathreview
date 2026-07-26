## Solution plan

**Issue:** [Add a safety event count to the health check endpoint](https://github.com/ascherj/pathreview/issues/68)

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
The root cause of this issue is the logic to fill `safety_events_last_hour` was never implemented in /health API end points. 

Expected behavior is best portrayed through an example: Suppose `SafetyMonitor` records 8 safety events, the `/health` handler should respond with 8 for `safety_events_last_hour`. Instead, the current returns 0 (because it was never implemented).


### Map
<!-- Which files, functions, or modules are involved?
List the specific files you expect to touch. -->
- `health_check()` in `api/routes/health.py`
- `get_event_count()` in `safety/monitoring.py`

### Plan
<!-- What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. import SafetyMonitor object in `health.py` using existing redis client
2. on line 81, add the result of `SafetyMonitor.get_event_count()` on  every valid event type through `SafetyMonitor.VALID_EVENT_TYPES` to get a total count of all events

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
It takes `SafetyMonitor.VALID_EVENT_TYPES`, and it should produce event count based on different event types.

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
**Where does `health.py` get a Redis client?** `health.py` builds one from `settings.redis_host` / `settings.redis_port`, but those aren't defined in `config` — only `redis_url` is, so that construction actually throws today.
- *Next step (done):* I checked the other modules in `api/routes/` — none build their own Redis client; the codebase's convention is FastAPI `Depends(...)` providers (`get_db` in `core/database.py`, `get_current_user` in `api/middleware/auth.py`). So my plan is to add a `get_redis()` provider in a new `core/redis.py`, built from `settings.redis_url` (the attribute that exists), and inject it — this fixes the broken construction *and* gives `SafetyMonitor` a client.
- *Open question for the maintainer:* whether fixing the `redis_host` construction belongs in this PR or a separate issue.

**1-hour vs 24-hour window.** The field is named `safety_events_last_hour`, but `get_event_count()` doesn't enforce a window — the Redis keys are counters with a 24h TTL, so it's really a rolling ~24h count.
- *Next step:* keep the field name and implement the sum for this issue, document the approximation in the PR description, and propose true hourly windowing (time-bucketed keys) as a follow-up issue rather than expanding scope here.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
- **Redis is down when `/health` runs** → `get_event_count()` (or `ping()`) raises → catch it, log `safety_events_check_failed`, and return `safety_events_last_hour = 0` so the health check degrades gracefully instead of 500-ing.
- **No safety events recorded yet** → the Redis keys don't exist → `get_event_count()` returns `0` (via `int(count) if count else 0`) → total `0`.
- **Only some event types have counts** → summing over `VALID_EVENT_TYPES` still works; missing keys contribute `0`.
- **An event type outside `VALID_EVENT_TYPES`** → not counted, by design (`log_event()` already rejects unknown types).