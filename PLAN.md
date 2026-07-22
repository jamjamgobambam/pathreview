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
Where does `health.py` get a Redis client? `health.py` does define a Redis client based on `settings.redis_host` and `settings.redis_port`, which are not defined in `config`'s `settings`. I'm not sure if I can go ahead and implement a fix for that, and if I can, what should be the host and port for Redis.


Also, the field specifies safety events in the last hour, but the function get_event_count() doesn't reinforce the timeframe of last hour. Instead, it uses the last 24-hour window. This gap is misleading, but I'm not sure if I can implement this part, since the scope reaches further beyond what the issue staed. 

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
If any error comes up in the process of calling `SafetyMonitor.get_event_count()`, a specific error should be given instead of a generic error.