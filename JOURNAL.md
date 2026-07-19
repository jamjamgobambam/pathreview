## Week 7 — Issue selection

**Issue link:** [Orchestrator catches all exceptions from tool calls and continues without logging the failure](https://github.com/ascherj/pathreview/issues/44)

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The core agent orchestrator in `agent/orchestrator.py` currently uses a broad exception handler that catches and silences any errors that occur when a tool is executed. This is problematic because when a tool fails (e.g., due to an API error or bad data), the failure is not logged anywhere. The agent just continues on, often producing an incomplete or inaccurate review without any indication to the user or developer that something went wrong. A successful fix will ensure that any exception from a tool call is properly logged, making the system more robust and easier to debug.

**Branch name:** `fix/44-orchestrator-silent-failure`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger