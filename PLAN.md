## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user #43](https://github.com/ascherj/pathreview/issues/43)

### Understand
The root cause is that `Orchestrator` never clears cached tool results between
separate review requests for the same profile.

- `Orchestrator.__init__` creates a single `ContextManager()` instance that
  lives for the lifetime of the orchestrator (`agent/orchestrator.py:29`).
- `Orchestrator._execute_tool` checks/stores results in that cache keyed only
  by `tool_name + sha256(tool_input)`, with no TTL and no profile/session
  scoping (`agent/orchestrator.py:150-162`).
- `SessionStore.delete()` exists (`agent/memory/session_store.py:68-81`) but
  is never called anywhere in `agent/orchestrator.py`. `run()` only ever
  merges old session state into new state and re-saves it
  (`agent/orchestrator.py:47-49`, `:65-67`) — it never clears anything.

**Expected behavior:** a new review request for a profile always runs the
plan's tools fresh and returns current data.

**Actual behavior:** if the same `Orchestrator` instance serves two reviews
for the same profile with the same tool input (e.g. an unchanged GitHub repo
name), the second review reuses the first review's cached result instead of
re-executing the tool.

### Map
Files/functions expected to change:

- `agent/orchestrator.py`
  - `Orchestrator.run()` — call `session_store.delete(profile_id)` (or an
    equivalent per-profile cache reset) at the start of a run, before loading
    any prior state.
  - `Orchestrator._execute_tool()` — scope the `ContextManager` cache key by
    profile/session, or clear the relevant entries at the start of `run()`,
    so cache hits can't cross separate review requests.
- `agent/memory/context_manager.py`
  - Possibly add a `clear()` / `clear_for_session()` method if the fix scopes
    invalidation through `ContextManager` rather than only `SessionStore`.
- `agent/memory/session_store.py`
  - No behavior change expected; `delete()` already exists and should just
    start being called.
- `tests/unit/test_orchestrator_session_state.py`
  - Already has a failing reproduction test; update/extend it to assert the
    fixed behavior once the change lands.

### Plan
1. Add a `ContextManager.clear()` method (or similar) to remove cached tool
   results for a given run.
2. In `Orchestrator.run()`, before building/executing the plan, clear the
   `ContextManager` cache and call `self.session_store.delete(profile_id)`
   if a session store is configured, so the review starts from a clean
   slate rather than inheriting entries from a prior review.
3. Keep `session_state` (loaded via `session_store.get`) only for whatever
   legitimate cross-review data it's meant to carry (if any) — confirm with
   the codebase/tests whether `session_state` should persist anything at all,
   or whether it should be removed as dead weight once caching is fixed.
4. Update `tests/unit/test_orchestrator_session_state.py` so the existing
   reproduction test now asserts `call_count == 2` and passes.
5. Add a second test confirming that within a *single* `run()` call, the
   in-request memoization behavior (calling the same tool with the same
   input once) is preserved — the fix should only stop caching *across*
   separate `run()` calls, not remove memoization within one call.

### Inputs & outputs
- **Input:** `profile_id` (str) and `profile_data` (dict) passed to
  `Orchestrator.run()`, same as today.
- **Output:** `run()`'s returned dict (`profile_id`, `tool_results`,
  `cached_results`) is unchanged in shape. The only behavioral change is that
  `tool_results` reflects fresh tool execution for each `run()` call for a
  given `profile_id`, instead of being served from a prior call's cache.

### Risks & unknowns
- Unsure whether `ContextManager` is meant to memoize *within* a single
  `run()` only, or whether some other caller relies on cross-run caching for
  performance — need to check for other callers/tests before removing it
  outright.
- If `Orchestrator` is instantiated as a singleton shared across concurrent
  requests for *different* profiles (e.g. in a FastAPI app), clearing on
  every `run()` could interact badly with concurrency; need to check how/where
  `Orchestrator` is wired up in `api/` before assuming single-threaded use.
- `session_state` is loaded but its fields are never distinguished from fresh
  `results` before being merged and re-saved — unclear if any downstream code
  depends on that merged history, or if it's fully unused.

### Edge cases
- First-ever review for a profile (no prior session state) — `session_store.get`
  returns `None`/`{}`; `delete()` on a nonexistent key should be a no-op.
- `session_store` not configured (`None`) — cache-clear logic must not assume
  a session store exists (matches current `if self.session_store:` guards).
- Two different profiles with tool inputs that hash identically (e.g. same
  GitHub repo name reused by two users) — cache must not leak between
  *different* profile IDs, not just between repeat reviews of the same one.
- Repeated tool execution *within* the same `run()` call (e.g. the same tool
  invoked twice in one plan with identical input) should still be memoized —
  only cross-run caching is the bug.
