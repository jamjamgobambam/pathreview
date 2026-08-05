# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The agent orchestrator's plan-execute loop wraps every tool call in a broad
`except Exception` block that silently swallows failures and moves on to the
next step. When a tool call fails partway through generating a review, the
orchestrator has no way to record that anything went wrong, so it produces a
review with missing sections and gives the user no indication of the
failure. A successful fix adds proper error logging in `agent/orchestrator.py`
and `agent/error_handling.py` so tool failures are captured and surfaced
instead of disappearing silently, without changing the orchestrator's overall
control flow.

**Branch name:** fix/44-log-tool-call-failures

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ericitem/pathreview/commit/5f573fb

**Reproduction summary:**
Added `tests/unit/test_orchestrator.py`, which runs a fake tool that fails
the same way every real tool in `agent/tools/` fails (returns
`ToolResult(success=False, ...)` internally instead of raising) through the
actual `Orchestrator.run()`. The test confirms the orchestrator never checks
`result.success`: it stores the failed tool's output as an indistinguishable
empty dict and logs `tool_executed ... success=True` with no error/warning
log anywhere, matching the issue's reported symptom exactly.

**PLAN.md link:** https://github.com/ericitem/pathreview/blob/fix/44-log-tool-call-failures/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
- Whether failed tool results should be cached by `ContextManager` the same
  way successful ones are (currently they are, unconditionally) needs a
  decision before implementation.
- Whether to wrap successful `tool_results` values in the same envelope as
  the fixed failure shape, or keep the two shapes different, is an open
  design question -- see PLAN.md Risks & unknowns.
- The mypy pre-commit hook is currently broken in this dev environment
  (pre-existing untyped functions in the touched modules, plus a
  numpy/mypy stub incompatibility under Python 3.14) independent of this
  issue; unconfirmed whether CI hits the same problem. Needs checking before
  the Week 9 PR.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`: `Orchestrator.run()` (`agent/orchestrator.py`)
now branches on `result.success` instead of unconditionally logging
`success=True` and storing `result.data`; a failing tool now logs
`tool_execution_failed` at error level and stores `{"error": ..., "success":
False}`. `_execute_tool()` no longer caches failed results (resolves the
caching risk from `PLAN.md`). `retry_with_backoff(max_retries=0)` in
`agent/error_handling.py` now raises `ValueError` instead of silently
returning `None`. All 5 `PLAN.md` sub-tasks are done. Test coverage expanded
from 1 to 7 cases in `tests/unit/test_orchestrator.py`, plus 4 new cases in
`tests/unit/test_error_handling.py` -- 11 total, all passing. Baseline
established before touching anything (`make check` / `make test-unit`); full
suite after the change is 53 failed / 386 passed, matching the documented
pre-existing 53-failure baseline exactly, with zero new failures.

**Next steps:**
Open the draft PR, request peer/mentor review through the course Slack
workflow, and address any feedback before marking it ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/903

**Branch:** `fix/44-log-tool-call-failures`

**What you built:**
`Orchestrator.run()` no longer trusts a tool call to have succeeded just
because it didn't raise. Every tool in `agent/tools/` catches its own
exceptions and returns `ToolResult(success=False, error=...)` instead of
raising, so the orchestrator now checks `result.success` explicitly: on
failure it logs an error with the real error message and stores a
distinguishable failure shape instead of an empty dict tagged as a success.
Also fixed a related bug where failed results were being cached and replayed
as false "cache hits," and a latent `max_retries=0` bug in the retry
decorator that silently returned `None`.

**Tests added or updated:**
`tests/unit/test_orchestrator.py` (expanded 1 -> 7 cases: the original
reproduction now passing, a success-path regression check, a tool that
raises directly, the pre-existing unknown-tool path, independent multi-tool
outcomes, and both directions of the caching fix) and new
`tests/unit/test_error_handling.py` (4 cases: the `max_retries=0` guard plus
baseline retry/success/exhaustion behavior that had zero prior coverage).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Neither box is checked as a blanket pass -- both commands fail
**repo-wide** due to a large pre-existing baseline unrelated to this issue
(documented in the PR's "Notes for Reviewers" and in Week 7/8 entries above):
182 pre-existing `ruff` errors, 52 files needing `black` reformatting, `mypy`
crashing on a numpy/Python-3.14 stub incompatibility in this local venv
before it reaches any changed file, and 53 pre-existing unrelated
`test-unit` failures. What's verified instead: this contribution introduces
**zero new failures** against that baseline -- confirmed failure counts
before and after for every check, see the PR description for exact numbers
and commands.

**Draft PR feedback received from:** none. A peer/mentor review request was
prepared for the course Slack workflow, but review was not obtained before
the submission deadline. With the deadline close, I made the call to submit
without it rather than hold the PR in draft indefinitely -- noting this
openly here rather than marking the review step as complete.
