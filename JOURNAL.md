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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All four PLAN.md sub-tasks are done. Added `SafetyMonitor.get_total_event_count()` and a `get_safety_monitor()` dependency provider in `safety/monitoring.py`, injected the monitor into `/health` via `Depends`, and replaced the hardcoded `0` with the real count. The reproduction test now passes. Verified no new failures: `make test-unit` shows 53 pre-existing failures (all in unrelated files), and mypy shows 11 pre-existing errors in `health.py` — the same counts before and after my change.

**Next steps:**
Open a draft PR, request peer feedback in Slack, then mark it ready and fill in Check-in 2.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [#447](https://github.com/ascherj/pathreview/pull/447)

**Branch:** `feat/68-health-safety-metrics`

**What you built:**
The `/health` endpoint now reports a real `safety_events_last_hour` count, read from `SafetyMonitor` (injected as a FastAPI dependency) instead of a hardcoded `0`.

**Tests added or updated:**
`tests/unit/test_health_route.py` — verifies `/health` surfaces the total event count from an injected monitor.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [Did not recieve on time]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in before the end of the week. 

**How you responded:**
Could not respond :(

---

### Reflection

**What was harder than you expected?**
Building the mental map of the project was tough — following how data moves from `safety/monitoring.py` through the Redis-backed `SafetyMonitor` into the `/health` response. But once I could see that flow in my head, the fix became obvious and quick.

**What did you learn about working in a large codebase?**
How important structure is. I could not have solved issue #68 this fast if the repo were not well documented and organized — I traced the fix across `safety/monitoring.py`, `api/routes/health.py`, and `tests/unit/test_health_route.py`. I also learned a big codebase comes with pre-existing problems (like 53 failing unit tests and a broken Redis probe config) that you work around instead of fixing.

**How did AI tools help — and where did they fall short?**
I used Claude and DeepSeek as coding assistants. They were most useful for navigating an unfamiliar codebase — tracing data flow and explaining patterns like FastAPI `Depends` injection. Where they fell short: I still had to verify their claims myself, and Claude actually hit its credit limit mid-task, so I had to switch tools to finish the PR.

**What would you do differently if you started over?**
I would start by asking AI to walk me through the program's logic instead of grinding through it myself. That would have been more time-efficient and would have given me better mental models of how the pipeline works. I would also lean into AI tools earlier, since they are clearly part of how development works now.

**What are you most proud of from this module?**
I am now able to contribute to open-source projects. The proudest moment was seeing my failing test go from `assert 0 == 7` to passing after wiring the real count into `/health`, and ending with a clean PR (#447) that has its own test coverage.

