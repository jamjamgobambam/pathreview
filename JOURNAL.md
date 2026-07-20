## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The /health endpoint is currently written as a placeholder and does not return the safety metrics for the last hour as intended. The fix is to read the actual count from the safety monitoring system and include it in the response. This lets operators quickly check recent safety activity without using the monitoring dashboard. I chose this as a Tier 1 issue since it's a contained, single-file fix that let me get familiar with the FastAPI routing and safety-monitoring modules before taking on something larger.

**Branch name:** fix/68-safety-events-health-check

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger