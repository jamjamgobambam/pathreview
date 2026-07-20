## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The /health endpoint is currently written as a placeholder and does not return the safety metrics for the last hour as intended. The fix is to read the actual count from the safety monitoring system and include it in the response. This lets operators quickly check recent safety activity without using the monitoring dashboard.

**Branch name:** fix/68-safety-events-health-check

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger