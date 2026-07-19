## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint currently reports basic service status, but it does not expose recent safety activity. This issue adds a `safety_events_last_hour` field so operators can monitor how active the safety layer has been without checking a separate dashboard. The change will likely involve the health route and the safety monitoring helper that computes the count. A successful fix will keep the existing health check behavior intact while adding the new metric to the response.

**Branch name:** fix/68-safety-event-count-health

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue selection notes:**
This issue is a good fit because it is a Tier 1 task with a clearly defined scope and expected outcome. I located the files referenced in the issue, understand that the goal is to expose a new `safety_events_last_hour` field in the health endpoint, and confirmed there are no blockers or dependencies. Based on the estimated effort, I believe it is realistic to complete within the Week 8–9 timeline.