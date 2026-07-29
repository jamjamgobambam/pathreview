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

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]