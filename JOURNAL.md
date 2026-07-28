# JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

The agent currently stores its state only in memory while it is processing a review. If the API server restarts, the running review loses its progress and has to start over. This issue affects the agent orchestration and state management components, where the workflow state is not persisted. A successful fix will save the agent's progress so long-running reviews can continue after a restart instead of starting over.

**Issue selection reasoning:**

I reviewed the issue scope and confirmed that the affected area is mainly the agent orchestration and state management code. The issue is larger than a small bug because it may require persistence, restart recovery, and tests, but the expected behavior is clearly described. I am comfortable working with Python backend code and Redis, and I can divide the work into smaller steps such as understanding the current state flow, adding persistence, and testing recovery after a restart. Although it is a Tier 3 issue, I believe it is challenging but realistic within the Module 3 timeline.

**Branch name:** fix/47-agent-state-persistence

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
(To be added after pushing this commit.)

**Reproduction summary:**

I ran the application locally and traced the complete review workflow. By inspecting the orchestrator and session store, I found that session state is loaded before execution but saved only after all tools complete. This means intermediate progress may be lost if the API restarts before the final save.

**PLAN.md link:**
(To be added after pushing.)

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**

I still need to verify the best checkpoint strategy and whether completed tools should be skipped when resuming a saved session.