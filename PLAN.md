## Solution plan

**Issue:** [#43 — Agent session state is not cleared between reviews for the same user](https://github.com/ascherj/pathreview/issues/43)

### Understand

**Root cause.** The `Orchestrator` memoizes tool results in an in-memory
`ContextManager` (`agent/memory/context_manager.py`) that is created **once**
in `Orchestrator.__init__` (`orchestrator.py:29`) and therefore survives across
`.run()` calls on a long-lived (singleton) orchestrator. On a second review the
memoization key is byte-identical, so the tool is never re-executed:

- The key is `hash(tool_input)`, and `tool_input` for `github_tool` is only
  `{github_username, repo_name}` (`orchestrator.py:94-97`). If the user edits a
  project but the repo name is unchanged, the hash is identical → cache hit →
  stale result served.
- `market_analyzer` gets a constant `{"detected_skills": {}}`
  (`orchestrator.py:130`), so its hash never changes → permanent cache hit after
  the first run.

A second, related defect is in the Redis persistence layer: `run()` loads the
prior session and does `session_state.update(results)` (`orchestrator.py:66`),
which **accumulates keys forever**. If a later review drops a tool from the plan
(e.g. the project that triggered `github_tool` was deleted), the old result
still lingers in the persisted state. Note: the loaded `session_state` is only
ever written back, never read to make a decision — so Redis today *hoards*
stale data rather than *serving* it.

**Expected vs. actual.**
- *Expected:* each new review starts clean, so tools re-run against the current
  portfolio and the persisted state reflects only the current review.
- *Actual:* a reused orchestrator serves prior in-memory results, and the Redis
  session accumulates results from tools no longer in the plan.

### Map

Files/functions involved:

- `agent/orchestrator.py` — **primary fix**
  - `Orchestrator.run` (`:31`) — where the in-memory cache leaks across runs and
    where prior session state is merged in on persist.
- `agent/memory/context_manager.py` — add a `clear()` method for per-run reset.
- `agent/memory/session_store.py` — no change expected (interface already has
  `get`/`set`/`delete`); read-only reference.
- `tests/unit/test_orchestrator_stale_cache.py` — the two existing failing
  regression tests that define "done" (already committed).

Files I expect to touch:
1. `agent/orchestrator.py`
2. `agent/memory/context_manager.py`
3. `tests/unit/test_orchestrator_stale_cache.py` (only if I add extra cases)

### Plan

1. **Add `ContextManager.clear()`** — reset `self.results = {}` with a log line.
   Keeps memoization a *within-run* optimization instead of a cross-run cache.
2. **Reset the in-memory cache at the start of each review** — call
   `self.context_manager.clear()` at the top of `Orchestrator.run` (before the
   plan executes). This fixes variant 1: a reused orchestrator re-runs its tools
   because the identical-hash cache entries from the previous review are gone.
3. **Stop accumulating stale keys in the persisted session** — replace
   `session_state.update(results); self.session_store.set(profile_id, session_state)`
   with persisting only the **current run's** `results`
   (`self.session_store.set(profile_id, results)`). Since the loaded state is
   never read for a decision, dropping the merge is safe and fixes variant 2.
4. **Run the regression tests** — `pytest tests/unit/test_orchestrator_stale_cache.py -v`
   must go from failing → passing. Then run the full unit suite to confirm no
   regressions elsewhere.
5. **Update `JOURNAL.md`** — record the fix, the before/after, and the passing
   test result.

### Inputs & outputs

- **Input:** unchanged public API — `Orchestrator.run(profile_id, profile_data)`.
- **Output / behavior change:**
  - Each `run()` re-executes its planned tools instead of returning cached
    results from a previous `run()` on the same instance.
  - The persisted Redis session for a profile contains only the tools from the
    most recent review (no orphaned keys).
  - No signature changes, no new config, no schema change.

### Risks & unknowns

- **Losing intra-run memoization benefit.** Clearing per-run is intended; a tool
  with the same `tool_input` appearing twice *within one plan* is still
  deduped, so no meaningful performance loss. (Real content-aware caching —
  keying on portfolio content instead of repo name — is a larger, separate
  change and out of scope for this Tier-1 fix.)
- **Is the loaded `session_state` used anywhere else?** Traced in the JOURNAL:
  it is written but never read to drive logic. I'll grep the repo once more to
  confirm no other caller depends on the merge behavior before removing it.
- **Orchestrator not yet wired into the API.** This is a design-level fix in the
  caching logic; I can only validate via unit tests, not an end-to-end HTTP
  flow. Acceptable — the tests reproduce both variants without Redis.

### Edge cases

- **Empty plan** (no `github_username`, no files, no readme, no resume) →
  `results` is `{}`; persisting `{}` should clear/overwrite prior state, not
  crash. Confirm `market_analyzer` is not added when `plan` is empty
  (guarded by `if plan:` at `orchestrator.py:127`).
- **`session_store is None`** (test 1's setup) → persist branch is skipped; the
  `clear()` fix alone must make tools re-run. Covered.
- **Same repo name, changed content** (test 1) → must re-run despite identical
  hash. Covered by the per-run `clear()`.
- **Tool dropped between reviews** (test 2) → dropped tool's key must be absent
  from persisted state. Covered by persisting only current `results`.
- **Tool raises** → error dict is stored under the tool name and persisted;
  behavior unchanged, just no longer merged with stale prior results.
