## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[Commit Link\]](https://github.com/zhannasunny/pathreview/commit/88e64c45e148a38c522007271bdf89738b70c4f9)

**Reproduction summary:**
Ran `Orchestrator.run()` twice for the same `profile_id` using an in-memory fake Redis and stub tools: review 1 with a GitHub project + README, then review 2 after removing the project. The stale `github_tool` result from review 1 was still present in the stored session after review 2, because `run()` loads the previous state and does `session_state.update(results)` instead of clearing it — confirming the bug.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Need to confirm how the API layer instantiates `Orchestrator`/`SessionStore` — whether a single `Orchestrator` (and its `ContextManager` memoization cache) is reused across reviews, which would be a second source of stale results beyond the Redis merge.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug is that the agent keeps reusing old session data for the same user instead of treating each new review as a fresh analysis. In the current flow, the session cache in session_store.py and the orchestration logic in orchestrator.py can preserve stale tool results across reviews, so updates to a user’s portfolio are not fully reflected. A successful fix would ensure that previous review state is cleared or invalidated when a new review starts, allowing the agent to rerun the relevant tools and produce up-to-date results.

**Branch name:** fix/43-agent-session-state-not-cleared-between-reviews

**Setup confirmation:** [YES] App runs locally at localhost:5173

**Cohort ledger:** [YES] Issue added to cohort ledger