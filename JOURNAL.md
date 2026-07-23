# JOURNAL.md — PathReview Contribution

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/44

**Issue title:** Orchestrator catches all exceptions from tool calls and continues without logging the failure

**Tier:** [x] Tier 2

**Problem summary:**
The agent's plan-execute orchestrator (`agent/orchestrator.py`) runs a list of tools in sequence and wraps each tool call in error handling. On close reading, logging is actually present at every level (via `structlog`, in both `_execute_tool()` and the outer `run()` loop, plus in `retry_with_backoff()` in `agent/error_handling.py`) — so the issue title is not fully precise. The real problem, confirmed by reading the code, is that when a tool fails, the orchestrator stores a per-tool `{"error": ..., "success": False}` entry inside the results dict and silently continues to the next tool. There is no top-level signal (e.g. an overall `partial_failure` flag) indicating that the returned review is incomplete, so a user receives what looks like a normal, complete review with a section silently missing, and nothing surfaces this at the API layer. A successful fix should add a clear, top-level indicator of partial failure so this can be surfaced to the user, without changing the existing (correct) logging behavior.

**"Is this issue right for me?" checklist reasoning:**
- Part 1: Confirmed — I can explain the problem and expected behavior without re-reading the issue (see problem summary above).
- Part 2: Tier 2 is a reasonable, if ambitious, step up from a first-time Tier 1 — chosen deliberately for the cross-module learning value (orchestrator + error handling + eventual API-layer surfacing) after weighing the risk with a mentor/AI sounding board.
- Part 3: Read `agent/orchestrator.py` and `agent/error_handling.py` in full. No dedicated test file exists for the orchestrator (`tests/unit/` has no `test_orchestrator.py`), so I reviewed `tests/unit/test_review_service.py` instead to understand this project's testing conventions (pytest, `unittest.mock`, fixture-heavy, class-based test suites) ahead of writing new tests for the orchestrator in Week 8-9.
- Part 4: No blockers or "blocked by #X" language found on the issue. Estimated effort per the issue is 4-6 hours, which is realistic for Weeks 8-9 given course workload.

**Branch name:** fix/44-orchestrator-swallows-tool-exceptions

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger