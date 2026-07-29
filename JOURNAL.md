# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health endpoint currently reports the service status but does not include information about recent safety-system activity. This makes it difficult for operaStors to quickly determine whether safety events have occurred without checking the monitoring dashboard. This issue affects the health route and the safety monitoring module. A successful fix will add a `safety_events_last_hour` field to the health-check response and ensure it reports the correct number of recent safety events.

**Selection notes ("Is this right for me?" checklist):**
This issue has a clearly defined scope and affects only a small part of the codebase. The issue description identifies the main files involved, making it easier to locate the relevant code. It is labeled Tier 1, which makes it appropriate for a first open-source contribution. I expect to understand how safety events are tracked, connect that information to the health endpoint, and update or add tests.

**Branch name:** feat/68-safety-event-health-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger