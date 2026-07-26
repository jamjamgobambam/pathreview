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
