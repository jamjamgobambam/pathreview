## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/43]

**Issue title:** [Agent session state is not cleared between reviews for the same user]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Is this right for me?**
- **Files involved:** `agent/orchestrator.py` (`run()`, keys the session store by `profile_id` and merges results with `session_state.update(results)`) and `agent/memory/session_store.py` (`get`/`set`/`delete`, Redis-backed with a 1-hour TTL). A separate in-memory memoization layer in `ContextManager` also needs to be traced since it interacts with the same cache-hit path.
- **Estimated time:** ~2-3 hours — most of it will go to tracing how `Orchestrator.run()` and `ContextManager` interact before touching any code, since the fix needs to target the real source of staleness rather than just patching a symptom.
- **Prerequisites:** Comfortable with Python and Redis key/TTL basics; no new dependencies needed. Local app setup (below) is already working.

**Problem summary:**
Currently, `Orchestrator.run()` keys the session store by `profile_id` (a per-user identifier) instead of a per-session ID, so tool outputs from a prior run get merged into the current run's results via `session_state.update(results)`. This causes the orchestrator to reuse stale tool outputs instead of fetching fresh data when a portfolio is updated, so users who request follow-up reviews are served outdated information that ignores their recent changes. A successful fix will implement proper session-aware cache keying and invalidation so that portfolio updates force the orchestrator to re-run analysis tools instead of merging in old cached state. Ultimately, this ensures every review delivers accurate, real-time insights rather than recycled state.


**Branch name:** [fix/43-session-state-not-cleared]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/zora123-svg/pathreview/commit/cf3e199f6c3e422f4a982dbf780565d3c108919e] (branch `fix/43-session-state-not-cleared`)

**Reproduction summary:**
Added `tests/unit/test_orchestrator_session_state.py`, which runs `Orchestrator.run()` twice for the same `profile_id` using a fake in-memory session store — first with a profile that triggers both `github_tool` and `tech_detector`, then again with a profile that only triggers `github_tool`. The test fails: the persisted session state after the second run still contains the first run's stale `tech_detector` result, confirming `session_state.update(results)` in `agent/orchestrator.py` never clears data from a prior review before merging in the current one.

**PLAN.md link:** [https://github.com/zora123-svg/pathreview/blob/fix/43-session-state-not-cleared/PLAN.md]

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm whether any other part of the app reads the Redis `session:{profile_id}` key expecting cumulative history across reviews (would affect how aggressively I can change the keying/merge behavior) — see Risks & unknowns in PLAN.md.
