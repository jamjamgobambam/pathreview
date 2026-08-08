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



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review comments yet. 

**How you responded:**
No changes were made. 

---

### Reflection

**What was harder than you expected?**
Writing the comprehensive unit tests was more challenging than expected. 

**What did you learn about working in a large codebase?**
I learned that a simple one-line code change often requires a lot more code in testing just to make sure it works. In a larger project, making sure errors are logged properly is just as important as the feature itself so others can debug issues later.

**How did AI tools help — and where did they fall short?**
AI tools were great for generating the boilerplate structure for the 44 new tests and pointing out all the places that needed the logging update. But they struggled with the specific mock setup our test suite needed, so I had to go in and manually fix the assertions for the logger calls.

**What would you do differently if you started over?**
I would spend more time looking at how the existing tests mock dependencies before writing my own. I jumped straight into writing the tests and had to backtrack to fix the mocking setup, which cost me some time.

**What are you most proud of from this module?**
I'm proud that I was able to figure out the potential problem just by reading the code in the selected files, and it turned out to be completely correct.