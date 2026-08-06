## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user (#43)](https://github.com/ascherj/pathreview/issues/43)

### Understand

**Root cause.** The agent orchestrator caches tool outputs in two places, and
neither is invalidated when a new review begins:

1. **In-memory memoization** — `Orchestrator` holds a single
   `ContextManager` instance (`self.context_manager`) created once in
   `__init__`. `_execute_tool` checks this cache by `tool_name + hash(input)`
   before running a tool. Because a long-lived orchestrator is reused across
   reviews, a second review whose tool inputs are unchanged (e.g. the GitHub
   tool called with the same `github_username`/`repo_name`) gets a **cache hit**
   and returns the *previous* review's result instead of re-fetching the
   freshly updated portfolio.
2. **Redis-backed session store** — `Orchestrator.run` loads prior state via
   `session_store.get(profile_id)`, then merges the new results and re-persists
   under the same key. The key is only the profile ID, so stale keys from an
   earlier review are never cleared — they accumulate and leak into later runs.

**Expected vs. actual.**
- *Expected:* each review re-runs the tools against the current portfolio, so
  portfolio changes (new repos, updated READMEs, new skills) are reflected.
- *Actual:* the second review for the same profile replays cached tool outputs
  from the earlier run, silently ignoring portfolio changes.

Reproduced by [tests/unit/test_orchestrator_session_state.py](tests/unit/test_orchestrator_session_state.py):
`test_second_review_reexecutes_tools_after_portfolio_change` shows the second
run returns `{"call": 1}` instead of `{"call": 2}`, and
`test_new_review_does_not_inherit_previous_session_state` shows stale
`github_tool` state persisting into a fresh review.

### Map

Files I expect to touch:

- [agent/orchestrator.py](agent/orchestrator.py) — clear per-review state at the
  start of `run()` (reset `context_manager`, and clear/namespace the session
  store entry for the profile before executing the plan).
- [agent/memory/session_store.py](agent/memory/session_store.py) — the existing
  `delete()` method already supports clearing; confirm it is used, or add a
  review-scoped key helper if namespacing is chosen.
- [agent/memory/context_manager.py](agent/memory/context_manager.py) — add a
  `clear()`/`reset()` method so the orchestrator can drop memoized results
  between reviews without reconstructing the object.
- [tests/unit/test_orchestrator_session_state.py](tests/unit/test_orchestrator_session_state.py)
  — the reproduction tests become the regression tests once the fix lands.

### Plan

1. Add a `clear()` method to `ContextManager` that empties `self.results`.
2. At the start of `Orchestrator.run()` (before executing the plan), reset the
   in-memory context via `self.context_manager.clear()` so no memoized result
   from a previous review is reused.
3. Also clear the persisted session for that profile at the start of the review
   (`self.session_store.delete(profile_id)` — or write to a per-review
   namespaced key such as `f"{profile_id}:{review_id}"`) so stale Redis state
   cannot leak in. Decide between "clear" vs. "namespace" based on whether any
   caller relies on cross-review persistence (audit shows the loaded state is
   only merged and re-saved, so clearing is the low-risk choice).
4. Keep persisting the *current* review's results at the end so within-review
   memoization still works.
5. Run the reproduction tests plus the full `agent/` unit suite to confirm the
   fix and no regressions (`make test-unit`).

### Inputs & outputs

- **Input:** `Orchestrator.run(profile_id, profile_data)` — a profile ID and the
  current portfolio data for a single review.
- **Output / change:** each call re-executes the planned tools against the
  supplied `profile_data`; the returned `tool_results` reflect the current run,
  and the persisted session for `profile_id` contains only the current review's
  results (no stale keys from prior reviews). No change to the public method
  signature or the shape of the returned dict.

### Risks & unknowns

- **Within-review caching must survive.** The context cache still needs to
  memoize repeated identical tool calls *inside* one review; the reset must
  happen once at the start of `run()`, not per tool. Risk: clearing in the wrong
  place disables intended memoization.
- **Clear vs. namespace decision.** Namespacing by review ID preserves history
  but requires a review ID to be threaded into `run()` (not currently passed).
  Clearing is simpler but discards any intended cross-review persistence. Need
  to confirm via `agent/orchestrator.py` and `core/services/review_service.py`
  that nothing depends on reading a prior review's session state.
- **Redis availability in tests.** `session_store.py` imports `redis` at module
  load, which isn't installed in the bare interpreter; tests must inject a fake
  client (already done in the reproduction) and must not require a live Redis.
- **Concurrency.** If two reviews for the same profile ever run concurrently,
  clearing a shared `profile_id` key could race. Namespacing by review ID would
  avoid this; note as a follow-up if clearing is chosen.

### Edge cases

- **First-ever review** for a profile — no prior session exists; `delete`/reset
  must be a no-op, not an error.
- **Empty plan** (portfolio data yields no tools) — the persisted session should
  end up empty, not retain a previous review's tool results.
- **Tool raises / times out** — a failed tool result for the current review must
  not be masked by a stale successful result from a prior review.
- **Orchestrator with no session store** (`session_store=None`) — context reset
  must still run; the session-clear step must be guarded.
- **Missing/expired Redis key** — `get` returning `None` must be handled the
  same as a fresh review.
- **Same tool input, changed upstream data** — the GitHub-tool case where input
  hash is identical but live data changed must produce a fresh result.
