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


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `agent/orchestrator.py` — `ContextManager` is now created fresh inside `run()` instead of persisting on the `Orchestrator` instance across requests, and `_execute_tool()` now takes it as a parameter. Added `tests/unit/test_orchestrator.py` with 4 tests covering the regression (tool re-executes on a second review, results are fresh not cached, no cross-user leakage). Confirmed `make test-unit` (53 pre-existing failures, unrelated, 379 passed including my new tests) and `make check` (179 pre-existing errors, down slightly from the 182 baseline, no new errors introduced). Opened draft PR #485.

**Next steps:**
Share the draft PR in Slack for peer/mentor feedback, address any comments, then mark it ready for review before the deadline.

**Blockers:**
None currently.


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/485

**Branch:** fix/43-clear-session-state

**What you built:**
Fixed the root cause of #43 — `Orchestrator` was creating a single long-lived `ContextManager` instance that persisted across every review, silently returning cached tool results from a previous review instead of re-running tools for a user's updated portfolio. `ContextManager` is now created fresh inside `run()`, scoped to a single review, while still allowing legitimate within-review memoization.

**Tests added or updated:**
Added `tests/unit/test_orchestrator.py` with 4 tests: tool executes on first review, tool re-executes on a second review with the same input (core regression test for #43), second review returns fresh (not cached) results, and two different users don't share cached results.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(179 pre-existing lint errors and 53 pre-existing test failures remain, unrelated to this change and documented in the PR description; my changes introduce zero new failures/errors and add 4 new passing tests.)

**Draft PR feedback received from:** none