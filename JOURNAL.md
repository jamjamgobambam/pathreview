## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue is about a bug in the agent workflow where state from one review can carry over into a later review for the same user. That stale session information can cause the next review to behave incorrectly or reuse context that should have been reset. A successful fix would ensure each new review starts with a clean agent session so the behavior is consistent and predictable.

**Branch name:** fix/43-clear-agent-session-state

**Branch URL:** https://github.com/hfaugas/pathreview/tree/fix/43-clear-agent-session-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
This issue is a good fit for a Week 7 submission because it is focused on project setup and contribution workflow rather than a large feature implementation. The scope is limited enough for a first contribution, and the work mainly involves documenting or clarifying setup expectations rather than changing core application behavior.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hfaugas/pathreview/commit/720920c

**Reproduction summary:**
I reproduced the issue by inspecting the orchestrator’s session-handling flow in agent/orchestrator.py and confirming that prior session state is loaded for the same profile ID before a new review run starts. The current implementation merges a persisted session payload into the next run, which means stale context from an earlier review can leak into a later review unless that state is explicitly cleared.

**PLAN.md link:** https://github.com/hfaugas/pathreview/blob/fix/43-clear-agent-session-state/PLAN.md

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
I still need to confirm whether any part of the product intentionally relies on session reuse across runs before changing the persistence behavior, especially around how the session store and orchestrator interact for repeated reviews.
