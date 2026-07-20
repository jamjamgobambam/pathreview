## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` API endpoint currently reports basic service status but doesn't include any information about the safety monitoring system. This means operators have no way to see recent safety-related activity, like how many safety events triggered in the last hour, without separately opening the monitoring dashboard. The fix adds a new `safety_events_last_hour` field to the health check response, pulling that count from the existing safety monitoring logic in `safety/monitoring.py`. This affects the `api/routes/health.py` endpoint and the safety layer of the codebase, making it easier to monitor system health from one place instead of two.
**Selection reasoning:**
I chose this as a Tier 1 issue because it's my first time contributing to a large, unfamiliar codebase, and this task has a small, well-defined scope: two named files (`api/routes/health.py` and `safety/monitoring.py`), a clear before/after behavior, and an estimated effort of 2-4 hours. It also touches a part of the app (health/monitoring) that's easier to reason about in isolation compared to a deeper architectural change, which fits my current comfort level with the codebase.

**Branch name:** fix/68-safety-event-count-health-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
