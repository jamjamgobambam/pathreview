## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user — https://github.com/ascherj/pathreview/issues/43

### Understand
Root cause: `Orchestrator.__init__` (agent/orchestrator.py:29) creates a single `ContextManager` that lives for the lifetime of the `Orchestrator` object instead of being scoped to one `.run()` call. Tool results are memoized by `(tool_name, hash(input))`, so if the same `Orchestrator` instance handles more than one review — the normal usage pattern — results from an earlier review can be silently served on a later one. This is guaranteed to happen for `market_analyzer`, whose input is hardcoded to `{"detected_skills": {}}` (line 130) regardless of the profile's actual data, so its hash never changes and every review after the first gets a cache hit. Separately, the Redis-backed `session_state` loaded via `SessionStore.get(profile_id)` (line 49) is merged with `.update()` rather than cleared before each run (line 66), so stale keys from an old review could persist under the same `profile_id` across reviews.

Expected: a new review always re-runs tools against the current input and reflects only that review's data.
Actual: a second review (e.g. after a portfolio update) can reuse stale tool results instead of re-running the tools that generate them.

### Map
- `agent/orchestrator.py` — primary fix location: `Orchestrator.__init__`, `run()`, `_execute_tool()`, and `_build_plan()` (the hardcoded `market_analyzer` input).
- `agent/memory/context_manager.py` — likely needs a `clear()`/`reset()` method, or `run()` needs to construct a fresh instance per call.
- `agent/memory/session_store.py` — no change expected; `get`/`set`/`delete` are already correct in isolation.
- New test file — none exist yet for this module; will likely add `tests/unit/test_orchestrator.py` following existing `tests/unit/` conventions.

### Plan
1. Add a way to clear `ContextManager` between reviews (a `clear()` method, or reconstruct it at the top of `run()`) so tool memoization never crosses review boundaries.
2. Fix `_build_plan()` so `market_analyzer`'s input reflects the current run's actual detected skills instead of a hardcoded empty dict, removing the guaranteed cache collision.
3. Change `run()` to replace (not merge) `session_state` with the current review's `results` before calling `session_store.set()` — or call `session_store.delete(profile_id)` at the start of `run()`, if session state isn't meant to survive across reviews at all.
4. Write unit tests that call `Orchestrator.run()` twice for the same profile with different inputs and assert the results differ / no stale cache is served.
5. If `Orchestrator` gets wired into `review_service.py` (unclear if in scope for #43), manually verify against the issue's reported scenario end-to-end; otherwise note it as a follow-up.

### Inputs & outputs
Input: `Orchestrator.run(profile_id, profile_data)`, where `profile_data` includes resume_text, github_username, projects, files, etc.
Output: a `tool_results` dict reflecting only the current run's data, with no leftover entries from a prior review of the same or a different profile.

### Risks & unknowns
- `Orchestrator` isn't currently called anywhere in the app or existing tests, so there's no integration point to validate the fix end-to-end — only unit-level verification is possible right now.
- Unclear whether `session_state` is meant to support some legitimate cross-review reuse (e.g. intentional performance caching) or should be wiped every time — whether to "replace" vs. "delete" depends on that intent, which the issue doesn't specify. Worth confirming with the cohort lead.
- No existing tests to build from, so fixtures/conventions for this module need to be created from scratch.

### Edge cases
- First-ever review for a profile (no prior session state) — should behave identically to today.
- Two different profiles reviewed back-to-back on the same `Orchestrator` instance — results must not cross-contaminate between users.
- A tool that failed on a previous review (stored as `{"error": ..., "success": False}`) — a later review should retry it, not reuse the failure.
- Identical input resubmitted deliberately (e.g. user re-runs a review without changing anything) — decide whether tools should still always re-run, or whether within-review memoization of duplicate calls (not cross-review) is still desired.