## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that the The /health API endpoint returns service status but doesn't surface safety metrics. What is missing is a safety_events_last_hour field to the health check response. The fix would be adding a safety_events_last_hour field to the endpoint so that the so operators can monitor safety system activity without querying the monitoring dashboard. It affects safety/monitoring.py and api/routes/health.py part of the codebase. 

**Branch name:** https://github.com/proy19/pathreview/tree/fix/68-Add-a-safety-event-count-to-the-health-check-endpoint

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/e7f5832e3ecb9e2baa20782a788c2384aa696a34 

**Reproduction summary:**
I inspected health.py and confirmed safety_events_last_hour was hardcoded to 0 with a comment noting it was a placeholder, never calling into SafetyMonitor. Since I didn't have a live Redis/Postgres environment to hit /health directly, I reproduced the underlying logic gap in isolation — stubbing redis and structlog and driving SafetyMonitor.log_event() / get_event_count() directly — which confirmed the old single-key-with-resetting-TTL design had no way to return a true "last hour" count; it could only return an unbounded rolling total.

**PLAN.md link:** https://github.com/proy19/pathreview/blob/fix/68-Add-a-safety-event-count-to-the-health-check-endpoint/PLAN.md 


**Blockers or open questions:**
