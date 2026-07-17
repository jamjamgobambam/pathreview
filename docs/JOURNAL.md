## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** Tier 1

**Selection Reasoning:** I chose this Tier 1 issue as a good starting point because it is focused on a small, well-scoped change and gives me a manageable way to learn how this open source project is structured. It also connects to the existing safety monitoring code, which makes it a practical first contribution for someone new to the codebase.

**Problem summary:** The /health endpoint currently reports service status, but it does not show recent safety activity. That makes it harder for operators to monitor safety events without checking a separate monitoring dashboard. A successful fix adds a safety_events_last_hour value to the health response so that information is available directly from the endpoint.

**Branch name:** feat/68-safety-event-count-health-check

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger