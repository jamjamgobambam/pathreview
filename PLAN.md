## Solution plan

**Issue:** Add a safety event count to the health check endpoint
 #68 (https://github.com/ascherj/pathreview/issues/68)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause of this issue is that the code assigns 0 to the variable "safety_events_last_hour" automatically instead of counting the safety events. Also, the Redis Client goes unused, so it doesn't query safety event keys, and the route does not instantiate the SafetyMonitor class.

I expected the /health endpoint to query Redis and sum up the safety event counts across all valid event types, but the /health endpoint actually automatically sets this to 0. I also expected api/routes/health.py to interact with SafetyMonitor and fetch event counts, but instead it pings Redis for connection status but never imports or instantiates SafetyMonitor.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

Files: api/routes/health.py and safety/monitoring.py
Functions: health_check(db=Depends(get_db)) (within healthy.py) and class SafetyMonitor (within monitoring.py).

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Add an aggregation method to SafetyMonitor in safety/monitoring.py
2. Import "SafetyMonitor" in "api/routes/health.py"
3. Reuse the Redis Client and Query Safety Events in "api/routes/health.py"
4. Verify the fix

### Inputs & outputs
What does your fix take as input? What should it produce or change?
This fix takes each safety event as input and counts them. The /health endpoint will produce a JSON response containing the aggregated live safety count rather than a hardcoded 0.

### Risks & unknowns
What could go wrong? What are you still unsure about?

api/routes/health.py: Failing to wrap the safety query in a try-except block could crash the /health endpoint with a 500 error if Redis drops connection mid-request.

safety/monitoring.py: Doing single-key Redis reads in a loop (for event_type in VALID_EVENT_TYPES) adds sequential network latency to an endpoint meant for fast liveness probing.

### Edge cases
What inputs or states should your fix handle gracefully?
The following should be handled by my fix: Redis unreachable or connection refused, missing/non-existent event keys, and high volume of logged events.
