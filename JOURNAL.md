## Week 7 — Issue selection

**Issue link:** [link](https://github.com/ascherj/pathreview/issues/68)

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]



The /health API endpoint returns health status attributes such as status, dependencies and timestamps (`api/routes/health.py`). However, it does not account for safety events that happened in the last hour. This issue aims to add a safety_events_last_hour value to /health API endpoint result that grabs information from `safety/monitoring.py` so that operators can use /health alone to track the system's health status instead of querying the monitoring dashboard on their own too.

**Branch name:** feat/68-Add-a-safety-event-count-to-the-health-check-endpoint

**Setup confirmation:** [Y] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger

