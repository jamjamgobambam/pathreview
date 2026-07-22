## Week 7 — Issue selection
**Issue link:** https://github.com/ascherj/pathreview/issues/68
**Issue title:** Add a safety event count to the health check endpoint
**Tier:** Tier 1
**Problem summary:**
The /health API endpoint returns the basic service status but not surface safety metrics. Operators currently have to use the monitoring dashboard manually to track system activity. Implementing a safety_events_last_hour field in the health check response will expose this metric directly, requiring data flow modifications between safety/monitoring.py and api/routes/health.py.
**Branch name:** fix/68-health-endpoint-safety-count
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger