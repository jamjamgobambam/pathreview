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