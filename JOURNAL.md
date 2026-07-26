## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The agent’s plan-execute loop in agent/orchestrator.py currently catches any exception raised by a tool and continues as though the call succeeded. This hides failures and can produce incomplete reviews with missing sections without explaining the problem to the user. A successful fix would use the project’s error-handling logic in agent/error_handling.py to record the failure and surface a clear error instead of silently continuing.

**Branch name:** fix/44-orchestrator-catches-exceptions-with-no-log

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
