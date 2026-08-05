## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add  a safety event count to the health check endpoint


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The goal of this issue is to surface safety activity directly in the /health API endpoint response so system operators can monitor recent safety events without needing to inspect external monitoring dashboards. I need to a dynamic safety_events_last_hour integer field to the health check JSON payload.
Currently, the endpoint contains a hard-coded fallback placeholder for the safety count. 

**Branch name:** fix/68-add-safety-event-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue understanding:** This application needs a system status check so that it reports the actual number of safety recorded recently, instead of just 0.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
This issue does not generate any errors, it just does not allow the application to run properly. It masks the fact that the actual safety metrics aren't being queried from Redis.

**PLAN.md link:** [link to PLAN.md in your fork]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed steps 1 and 2 and added an aggregation method to SafetyMonitor in safety/monitoring.py, then imported "SafetyMonitor" in "api/routes/health.py".


**Next steps:**
For the rest of the week, I will be writing a test to ensure that api/routes/health.py works properly and debugging my code.

**Blockers:**
When I try to commit my changes, I keep getting errors. I need to debug my code and determine which errors were not created by me.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/874#issue-5066249657

**Branch:**
fix/68-add-safety-event-count

**What you built:**
I created module get_total_event_count() in safety/monitoring.py to count all safety events within a 24h window, imported SafetyMonitor and reused Redis client for safety_events_last_24h, and added tests/unit/test_health.py to ensure health.py was working properly after changes. Safety events are now logged as timestamped entries in a Redis sorted set rather than a flat counter, so safety_events_last_24h reflects a true trailing 24-hour window instead of an unknown value that could silently accumulate indefinitely under steady traffic.

**Tests added or updated:**
I created one test file: tests/unit/test_health.py. This test connects to a real local Redis instance and creates a SafetyMonitor, then logs three dummy safety events (two pii_detected, one injection_attempt). It calls the actual /health endpoint via FastAPI's TestClient and then asserts the response is 200 and that safety_events_last_24h is present and >= 3.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
none
