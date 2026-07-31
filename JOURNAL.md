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

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/950cac57c1089c5a6c4842dc30a31be5d5a4fec8

**Reproduction summary:**
I reproduced the issue by calling the `/api/health` endpoint in my local environment. Although the response already contains the `safety_events_last_hour` field, it always returns a placeholder value of `0`. After tracing the implementation, I found that `api/routes/health.py` hardcodes this value instead of retrieving actual safety event counts from the monitoring component.

**PLAN.md link:** https://github.com/vineeth-utd/pathreview/blob/fix/68-safety-event-count-health/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The health endpoint needs to report the total number of safety events across all valid safety event types. The remaining investigation is to determine the best way to aggregate these counts using the existing `SafetyMonitor` implementation while following the project's existing design patterns.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the aggregation logic in `SafetyMonitor` to compute the total safety event count across all valid safety event types and updated the `/health` endpoint to use the computed value instead of a placeholder. Added unit tests covering aggregation, empty Redis state, valid event types, and error handling. During implementation, I also identified that the health endpoint was creating Redis clients using undefined configuration fields and updated it to use the project's configured `redis_url`.

**Next steps:**
Run the remaining verification checks, prepare the pull request, request feedback on the draft PR, and update the documentation with the final PR link and testing summary.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/420

**Branch:** `fix/68-safety-event-count-health`

**What you built:**
Implemented `SafetyMonitor.get_total_event_count()` to aggregate safety event counts across all valid event types and updated the `/health` endpoint to report the computed value instead of a hardcoded placeholder. The Redis client initialization was also updated to use the project's configured `redis_url`, allowing the health endpoint to correctly retrieve Redis-backed safety event counts.

**Tests added or updated:**
Added `tests/unit/test_safety_monitor.py` covering aggregation across all valid safety event types, empty Redis state, validation that only supported event types are included, and graceful handling of Redis errors during event count retrieval.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none