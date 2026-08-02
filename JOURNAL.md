# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The `/health` API endpoint currently reports the status of the application's services, but it does not include information about recent safety system activity. The safety monitoring module already handles safety-related events, but that information is not exposed through the health check response. This issue affects the health endpoint in `api/routes/health.py` and the monitoring logic in `safety/monitoring.py`. A successful fix will calculate the number of safety events recorded during the last hour and return that number in a new `safety_events_last_hour` response field.

**Selection notes — “Is this right for me?” checklist:**

I selected this issue because it is labeled Tier 1 and is estimated to take approximately two to four hours. The issue has a focused scope and identifies the two main files that are likely to require changes. I have previous experience working with Python APIs, backend routes, validation logic, and tests, so the issue matches skills I have practiced in earlier projects. The expected result is also specific and testable: the `/health` response should contain a safety event count for the previous hour.

**Branch name:** `fix/68-safety-event-health-count`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/k-hetherington/pathreview/commit/9d48bbe)

**Reproduction summary:**

I reproduced Issue #68 by reviewing the implementation immediately before my fix and confirming that the `/health` endpoint always returned a placeholder value of `0` for `safety_events_last_hour`.

While investigating, I found that `SafetyMonitor` only stored cumulative Redis counters using `INCR`. Although `get_event_count()` accepted a `window_hours` parameter, the value was never enforced because events were not stored with timestamps. As a result, the application could not accurately report the number of safety events that occurred during the previous hour.

**PLAN.md link:** https://github.com/k-hetherington/pathreview/blob/fix/68-safety-event-health-count/PLAN.md

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

I wanted to determine the best Redis data structure for supporting rolling time-window queries while also automatically removing expired events.
