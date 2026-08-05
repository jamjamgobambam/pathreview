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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from PLAN.md step 2(a): `Orchestrator.run()` (`agent/orchestrator.py`) no longer loads the previous session blob and merges it with `session_state.update(results)` before persisting. It now writes only the current run's `results` back to the session store, so a tool that isn't part of this review's plan can no longer survive as leftover state from a prior review of the same `profile_id`. Grepped the codebase for other call sites that construct `Orchestrator`/call `session_store.get(`/`set(` outside the test file and found none, so the narrower fix (no new per-review session ID) is sufficient — resolves the "Risks & unknowns" open question from Week 8. The reproduction test in `tests/unit/test_orchestrator_session_state.py` now passes.

**Next steps:**
Add the companion test from PLAN.md step 5 asserting that legitimate intra-session continuity (same session, same input hash) still works via `ContextManager`, so the fix doesn't overcorrect. Then self-review against `docs/CONTRIBUTING.md`, run `make check`, and open a draft PR.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/43-session-state-not-cleared`

**What you built:**
`Orchestrator.run()` (`agent/orchestrator.py`) no longer loads the previous session state from Redis and merges it into the current run's results before persisting. It now writes only the current run's tool results back to the session store, so a tool that was part of an earlier review's plan but not this one can no longer linger in Redis under the same `profile_id`.

**Tests added or updated:**
`tests/unit/test_orchestrator_session_state.py`:
- `test_stale_tool_result_carried_into_review_where_tool_did_not_run` — reproduction test that runs two reviews for the same `profile_id` where the second review's plan omits `tech_detector`, and asserts the persisted session state no longer contains `tech_detector` afterward. Previously failing, now passes.
- `test_repeated_call_within_same_session_still_hits_context_cache` (new, added per PLAN.md step 5) — guards against overcorrecting: calls `run()` twice on the *same* `Orchestrator` instance with identical input and asserts the tool only executes once (`call_count == 1`), i.e. legitimate intra-session memoization via `ContextManager` still works after removing the cross-review `SessionStore` merge.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Confirmed via `git stash` comparison: baseline on this branch before the fix was 32 failed/257 passed on `test-unit`, with 8 unrelated files failing to collect due to pre-existing missing dev dependencies — `numpy`, `sqlalchemy`, `jose`, `tiktoken`, `pypdf`, `rank_bm25` — and 175 pre-existing repo-wide ruff errors, none in the file I changed. After the fix: 31 failed/258 passed — only the reproduction test flipped, no new failures. `ruff`, `black`, and `mypy` all pass cleanly on `agent/orchestrator.py`.)

**Draft PR feedback received from:** [name or Slack handle, or "none"]
