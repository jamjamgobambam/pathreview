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
