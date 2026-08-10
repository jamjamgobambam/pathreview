## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure #44

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

### Issue Fit & Selection Reasoning

* **Why Tier 2:** I have experience working in codebases with interacting services and feel comfortable tracing data flow across multiple modules (`agent/orchestrator.py` and `agent/error_handling.py`).
* **Checklist & Scope Fit:**
  * [x] **Understanding:** I can explain the current silent failure behavior and expected structured logging outcome in my own words.
  * [x] **Codebase Readiness:** I have located `agent/orchestrator.py` and `agent/error_handling.py`, reviewed the surrounding `run()` logic, and checked the corresponding unit tests under `tests/unit/`.
  * [x] **Scope & Time:** Estimated effort for this Tier 2 issue is around 8–12 hours, which easily fits within the Weeks 8–9 implementation timeline.
  * [x] **Dependencies & Ledger:** Verified there are no blocking unresolved issues, and checked the cohort ledger claims count.

**Problem summary:**
The orchestrator in the agent workflow is swallowing tool-call failures and continuing execution without surfacing enough diagnostic detail. In practice, a broken tool can fail in the background while the rest of the plan proceeds, making it hard to tell which tool failed, why it failed, or whether retries were already attempted. The issue affects the orchestration flow in agent/orchestrator.py and the retry handling in agent/error_handling.py. A successful fix would make these failures visible, structured, and actionable so the system can log them clearly and stop or handle them more intelligently when needed.

**Branch name:** fix/44-orchestrator-logging-issue

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/helpism/pathreview/commit/179625f44aa48d8df2ba3dd093e4ff8b96869253 

**Reproduction summary:**
I reproduced the issue by writing a unit test (`test_orchestrator_swallows_tool_failure_without_logging_exc_info`) that mocked a tool execution to raise an intentional `AttributeError`. I observed that while `orchestrator.run()` caught the failure and logged a generic error message, it completely omitted exception stack traces (`exc_info`) and silently swallowed intermediate retry attempts.

**PLAN.md link:** https://github.com/helpism/pathreview/commit/48a9500d21d2c7b4960d5d9d52c74c869d290c04 

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
While i was attempting to find the cause of the issue, i hit several roadblock (e.g. tracing the wrong problem and then being stuck). What are steps to take to systematically isolate a root cause without getting side-tracked by false leads? Thanks in advance.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix for Issue #44 by adding `exc_info=True` to the structured error logs in `agent/error_handling.py` (for intermediate retries) and `agent/orchestrator.py` (for top-level tool failures). I also updated `tests/unit/test_orchestrator.py` to assert that the exception stack trace is successfully captured. All coding sub-tasks from my PLAN.md are complete.

**Next steps:**
Open a draft pull request on GitHub, note the pre-existing unrelated test/linting failures in the description, and request a peer review in the class Slack channel.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/863
**Branch:** `fix/44-orchestrator-logging-issue`
**What you built:** Added `exc_info=True` to `agent/orchestrator.py` and `agent/error_handling.py` to ensure unhandled tool exceptions preserve their full stack trace in structured logs.
**Tests added or updated:** Updated `tests/unit/test_orchestrator.py` to verify that `structlog` captures `exc_info` when a tool crashes.
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
**Draft PR feedback received from:** Asked in Slack, but no feedback was received prior to the submission deadline.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?] The part of the project that was the hardest was finding the actual issue in
orchestrator.py and error_handling.py. Often times i found myself focused on the wrong function —
like `_build_plan` or the `retry_with_backoff` decorator — instead of the actual `except` blocks in
`run()` and `_execute_tool` where the `exc_info` was missing.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?] I think the biggest difference from a personal project is that you 
have to spend a lot of time just reading and understanding files like orchestrator.py and error_handling.py
before you can write any code i.e tracing how `_execute_tool` calls `_execute_with_timeout`, which wraps
`retry_with_backoff`, took a while to fully piece together. I also learned that you have to be okay with
leaving pre-existing broken tests alone as long as your specific fix (adding `exc_info=True`) works. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?] The AI tool helped in understanding the general idea of 
what orchestrator.py and error_handling.py were meant to do, and the purpose of functions like `run()`,
`_execute_tool`, and `retry_with_backoff`. It fell short in determining the exact way to resolve the
issue — it couldn't tell me which of the `logger.error` calls actually needed `exc_info=True` added,
so i had to trace that myself.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
One thing i would change would be my approach to resolving issue #44. I think i went
too quick into editing error_handling.py before fully understanding how orchestrator.py's `run()` loop
and `_execute_tool` actually used it in the context of the entire project. 
**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I'm most proud of the journey of understanding and resolving issue #44. I had never used structlog's
`capture_logs()` before this project. Taking the time to grasp how to use it to actually assert on
`exc_info` in the test is something i am proud of. 