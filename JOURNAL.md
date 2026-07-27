## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** The /health API endpoint returns service status but doesn't surface safety metrics

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, the `/health` endpoint only provides generic service status, lacking visibility into the safety system's activity without querying a separate monitoring dashboard. This issue requires adding a `safety_events_last_hour` field to the health check response to directly expose recent safety metrics. A successful fix will involve modifying the `api/routes/health.py` file to fetch this data from `safety/monitoring.py`, enabling easier operational oversight of safety components.

**Selection reasoning:**
I chose this Tier 1 issue because it aligns well with my current comfort level in exploring a large codebase. It has a tightly defined scope, modifying only two specific files (`api/routes/health.py` and `safety/monitoring.py`), which makes it an excellent first contribution. It allows me to trace a single straightforward data flow from the safety module to the API endpoint without getting overwhelmed by the broader architectural complexity.

**Branch name:** feat/68-health-safety-metrics

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/aayans314/pathreview/commit/1794be1341b3d76210a8709d74c246f55834dd75

**Reproduction summary:**
I added a failing unit test (`tests/unit/test_health_route.py`) that stands up a `SafetyMonitor` holding 7 recorded events, mocks the health check's dependency probes so it returns 200, and asserts the response's `safety_events_last_hour` matches. It fails with `assert 0 == 7`: `api/routes/health.py` hardcodes `safety_events_last_hour` to 0 and never reads from `safety/monitoring.py`.

**PLAN.md link:** [PLAN.md](PLAN.md)

