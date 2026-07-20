## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68#issue-4117410262

**Issue title:** Add a safety event count to the health check endpoint


**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In api/router/health.py file, the health check endpoint does not include a safety events count. There is a placeholder variable (safety_events_last_hour) which doesn't read the actual data.
But, in safety/monitoring.py file, there is a function that reads the safety events count from the database. I need to write helper functions to read the data from the database and update the health check endpoint to show the actual safety events count instead of a constant zero value.

**Branch name:** feat/68-add-safety-events-count-to-health-check

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
