# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/83

**Issue title:** Add a `GET /health` endpoint with dependency status checks

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The issue, or rather the improvement, is providing an endpoint that can be used to check the health of the application. Currently, the code is present that does the actual check (file `api/routes/health.py`), but there is no way that the check is exposed to the API nor any tests. A successful fix would add a route to the API that returns the health status of the application, including the status of its dependencies, and also include tests to ensure that this endpoint works as expected.


**Branch name:** feat/83-health-endpoint

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger