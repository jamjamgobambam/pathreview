## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The orchestrator caches agent state by user ID inside `agent/memory/session_store.py`. When a user submits a second portfolio review after updating their portfolio, the system reuses the cached tool results from their previous session instead of re-running the tools against the new portfolio data. This means the review a user receives can be based on stale information rather than what they actually just submitted. A successful fix would ensure each new review request triggers fresh tool execution (or properly invalidates/clears the cached session state) so results always reflect the current portfolio.

**Branch name:** fix/43-clear-session-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/akao335/pathreview/commit/4310aac

**Reproduction summary:**
Wrote `scripts/reproduce_43.py`, which runs the same `Orchestrator.run()` call twice in a row for the same profile_id and portfolio data using a stub tool that counts its own executions. The first review executes the tool (`tool_result_cache_miss`, `call_count: 1`). The second review returns a cache hit (`tool_result_cache_hit`) and never re-executes the tool (`call_count` stays at `1`), proving the orchestrator's `ContextManager` cache persists across separate reviews instead of resetting.

**PLAN.md link:** https://github.com/akao335/pathreview/blob/fix/43-clear-session-state/PLAN.md

**Walkthrough video (recommended):** (none recorded)

**Blockers or open questions:**
Still need to confirm how `Orchestrator` is instantiated in the FastAPI app (singleton vs. per-request) before finalizing the exact fix approach. Also need to check whether the Redis-backed `session_store` (separate from `ContextManager`) needs its own invalidation logic once the `ContextManager` issue is fixed.