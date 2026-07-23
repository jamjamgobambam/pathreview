## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** Tier 1

**Selection Reasoning:** I chose this Tier 1 issue as a good starting point because it is focused on a small, well-scoped change and gives me a manageable way to learn how this open source project is structured. It also connects to the existing safety monitoring code, which makes it a practical first contribution for someone new to the codebase.

**Problem summary:** The /health endpoint currently reports service status, but it does not show recent safety activity. That makes it harder for operators to monitor safety events without checking a separate monitoring dashboard. A successful fix adds a safety_events_last_hour value to the health response so that information is available directly from the endpoint.

**Branch name:** feat/68-safety-event-count-health-check

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

**Reproduction commit link:** https://github.com/trihiennguye-ux/pathreview/commit/efd3b6b7dd1a56278dc7cdd725542337b796cab9

**Reproduction summary:**
- I reproduced the issue through health check endpoint and check the logs for safety_events_check_failed error. I noticed the safety_events_last_hour return 0 instead of the actual value, this is because the endpoint does not read from the Redis-backed monitoring state.

**PLAN.md link:** https://github.com/trihiennguye-ux/pathreview/blob/feat/68-safety-event-count-health-check/docs/PLAN.md

**Blockers or open questions:**
