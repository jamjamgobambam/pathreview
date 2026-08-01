## Week 7 — Issue selection

**Issue link:** [Orchestrator catches all exceptions from tool calls and continues without logging the failure](https://github.com/ascherj/pathreview/issues/44)

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The core agent orchestrator in `agent/orchestrator.py` currently uses a broad exception handler that catches and silences any errors that occur when a tool is executed. This is problematic because when a tool fails (e.g., due to an API error or bad data), the failure is not logged anywhere. The agent just continues on, often producing an incomplete or inaccurate review without any indication to the user or developer that something went wrong. A successful fix will ensure that any exception from a tool call is properly logged, making the system more robust and easier to debug.

**Branch name:** `fix/44-orchestrator-silent-failure`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/8368de6757de9942cad639da5809277ec200ef8a

**Reproduction summary:**
I reproduced the issue by adding a temporary `raise RuntimeError("Test error")` inside `github_tool.py` and running the application. I noticed that the orchestrator caught the exception and printed a simple error string (`error='Test error'`), but didn't log the full error details, so you can't tell exactly which file or line of code failed.

**PLAN.md link:** https://github.com/vasubawa/pathreview/blob/fix/44-orchestrator-silent-failure/PLAN.md

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I added `exc_info=True` to all `logger.error` calls in `agent/orchestrator.py` and `agent/error_handling.py`. This makes structlog emit the full exception traceback whenever a tool fails, instead of just the error string. I also created `tests/unit/test_orchestrator.py` and `tests/unit/test_error_handling.py` with 44 new unit tests, including tests that specifically assert `exc_info=True` is present in the logged calls. All 44 pass.

**Next steps:**
Open a draft PR, request peer feedback in Slack, and fill in Check-in 2 with the PR link before Sunday.

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/508

**Branch:** `fix/44-orchestrator-silent-failure`

**What you built:**
Added `exc_info=True` to `logger.error` calls in `orchestrator.py` and `error_handling.py` to ensure structlog emits full exception stack traces when tools fail or retries are exhausted. This resolves the silent failure swallowing issue (Issue #44).

**Tests added or updated:**
Created `tests/unit/test_orchestrator.py` and `tests/unit/test_error_handling.py` with 44 tests to verify orchestrator flow, retry context logic, and specifically assert that `exc_info=True` is passed to the logger on failures.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none