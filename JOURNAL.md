## Week 7 — Issue selection
**Issue link:** https://github.com/ascherj/pathreview/issues/68
**Issue title:** Add a safety event count to the health check endpoint
**Tier:** Tier 1
**Problem summary:**
The /health API endpoint returns the basic service status but not surface safety metrics. Operators currently have to use the monitoring dashboard manually to track system activity. Implementing a safety_events_last_hour field in the health check response will expose this metric directly, requiring data flow modifications between safety/monitoring.py and api/routes/health.py.
**Branch name:** fix/68-health-endpoint-safety-count
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning
**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/2578ff266e9aabf44706292441ea468c8d028520)
**Reproduction summary:**
Requested the `/health` endpoint locally and verified the response omits the `safety_events_last_hour` metric entirely.
**PLAN.md link:** (https://github.com/10-49/pathreview/blob/fix 68-health-endpoint-safety-count/PLAN.md)
**Walkthrough video (recommended):** 
**Blockers or open questions:**
