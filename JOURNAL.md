## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** The /health API endpoint returns service status but doesn't surface safety metrics

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, the `/health` endpoint only provides generic service status, lacking visibility into the safety system's activity without querying a separate monitoring dashboard. This issue requires adding a `safety_events_last_hour` field to the health check response to directly expose recent safety metrics. A successful fix will involve modifying the `api/routes/health.py` file to fetch this data from `safety/monitoring.py`, enabling easier operational oversight of safety components.

**Branch name:** feat/68-health-safety-metrics

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
