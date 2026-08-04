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
https://github.com/GargiBhise/pathreview/commit/c17a60d

**Reproduction summary:**

I ran the application locally and traced the complete review workflow. By inspecting the orchestrator and session store, I found that session state is loaded before execution but saved only after all tools complete. This means intermediate progress may be lost if the API restarts before the final save.

**PLAN.md link:**
https://github.com/GargiBhise/pathreview/blob/fix/47-agent-state-persistence/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**
No blockers. The implementation was completed and submitted as PR #834.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

- Investigated the orchestrator flow and identified where session state is loaded and persisted.
- Implemented checkpoint-based session persistence after each successful tool execution.
- Verified that previously completed tool results can be restored from the session store.

**Next steps:**

- Add unit tests for checkpointing and resume behavior.
- Run validation checks.
- Open the pull request and update documentation.

**Blockers:**

The repository contains pre-existing mypy errors and unrelated failing unit tests that are outside the scope of this issue.

---

### Check-in 2 (end of week)

**PR link:**

https://github.com/ascherj/pathreview/pull/834

**Branch:**

`fix/47-agent-state-persistence`

**What you built:**

Implemented incremental session checkpointing so completed tool results are saved after each successful tool execution. When the API restarts, the orchestrator restores the saved session state and skips tools that have already completed, allowing the workflow to resume instead of restarting from the beginning.

**Tests added or updated:**

Created `tests/unit/test_orchestrator.py` covering:

- checkpoint persistence after successful tool execution
- restoring completed tools from session state
- execution without a session store

**Self-review confirmation:**

- [x] Focused orchestrator unit tests pass
- [x] Ruff checks pass
- [x] Python syntax validation passes

The repository contains pre-existing unrelated mypy errors and failing unit tests that were not introduced by this PR.

**Draft PR feedback received from:**

None