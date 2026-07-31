## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is currently written as a placeholder and does not return the safety metrics for the last hour as intended. The fix is to read the actual count from the safety monitoring system and include it in the response. This lets operators quickly check recent safety activity without using the monitoring dashboard. I chose this as a Tier 1 issue since it's a contained, single-file fix that let me get familiar with the FastAPI routing and safety-monitoring modules before taking on something larger.

**Branch name:** fix/68-safety-events-health-check

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hkumar30/pathreview/commit/44ad5ac

**Reproduction summary:**
I confirmed `SafetyMonitor`'s Redis counter works correctly in isolation (logging an event and reading it back returned 1), then called the real `/health` endpoint and found it always returns `safety_events_last_hour: 0` regardless, since `health.py` hardcodes that field and never reads from `SafetyMonitor`. I captured this as a failing test in `tests/unit/test_health.py`.

**PLAN.md link:** https://github.com/hkumar30/pathreview/blob/fix/68-safety-events-health-check/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Wiring `log_event()` into the three detector modules is needed for the count to ever be nonzero, but that's more than the issue's stated 2-4hr scope implies — planning to confirm with a mentor whether that belongs in this PR or a follow-up issue.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from `PLAN.md`: fixed the `settings.redis_host`/`redis_port` bug in `health.py` by parsing from `redis_url` instead, and replaced the hardcoded `safety_events_last_hour: 0` with a real `SafetyMonitor.get_event_count()` aggregation across all event types. Updated `tests/unit/test_health.py` — the old failing reproduction test now passes, plus added tests for zero-events, multi-type aggregation, and Redis-down degradation (5 tests total, all passing). Ran a baseline `make check`/`make test-unit` (via `git stash`) and confirmed my changes introduce no new test failures and only one new lint finding that matches an existing, unfixed pattern already in the same file.

**Next steps:**
Open a draft PR and request peer/mentor review in Slack, manually verify the fix against a running Postgres/Redis locally, then finalize and submit the PR by Sunday.

**Blockers:**
Resolved the open question above myself rather than waiting on a mentor: descoped wiring `log_event()` into the three detector modules, since none of them (`BiasDetector`, `PIIScrubber`, `PromptDefense`) are called anywhere outside their own tests — the safety pipeline isn't wired into review submission at all yet, which is a separate, larger issue than #68's stated scope. Documented this decision in `PLAN.md`.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** fix/68-safety-events-health-check

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]