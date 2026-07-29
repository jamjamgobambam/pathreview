## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user (#43)
https://github.com/ascherj/pathreview/issues/43

### Understand
The root cause is not in `session_store.py` (the Redis-backed store), which
is correctly keyed per-user with a TTL. The actual bug is in
`agent/orchestrator.py`. The `Orchestrator` creates a single `ContextManager`
instance in `__init__` (`self.context_manager = ContextManager()`). Because
the `Orchestrator` is long-lived (instantiated once and reused across
requests), this cache persists across separate calls to `run()`, including
separate reviews.

In `_execute_tool()`, before running any tool, the orchestrator computes
`input_hash = ContextManager.hash_input(tool_input)` and checks
`self.context_manager.get_tool_result(tool_name, input_hash)`. If a hit is
found, it returns the cached result immediately and never re-executes the
tool. The cache key only depends on `tool_name` + a hash of the tool's
input dict (e.g. `github_username` + `repo_name`). If a user updates their
portfolio but the specific fields fed into a tool are unchanged (e.g. same
repo name, even though the repo's contents changed on GitHub), the hash is
identical, so the second review silently returns stale data instead of
fresh results.

Expected behavior: each new review request should produce fresh tool
results reflecting the user's current portfolio state.
Actual behavior: a second review for the same user can return byte-for-byte
identical results to a previous review, even when the underlying data
(e.g. repo content) has changed.

### Map
Files expected to be touched:
- `agent/orchestrator.py` — `Orchestrator.__init__`, `Orchestrator.run()`,
  and `Orchestrator._execute_tool()`. Need to change how (and whether) the
  `ContextManager` cache persists across separate `run()` calls.
- `agent/memory/context_manager.py` — may need a new method (e.g. `clear()`)
  or a change so a fresh `ContextManager` is created per review rather than
  per orchestrator instance.
- `scripts/reproduce_43.py` — reproduction script already added; will be
  extended or kept as a regression check.
- Possibly a new/updated test file, e.g. `tests/test_orchestrator.py`, to
  cover this behavior with an automated test (not just the manual repro
  script).

### Plan
1. Change `Orchestrator` so `context_manager` is scoped to a single `run()`
   call instead of the whole orchestrator instance — e.g. instantiate a new
   `ContextManager()` at the top of `run()` instead of in `__init__`, so
   each review starts with a clean cache.
2. Update `_execute_tool()` (and any other method that references
   `self.context_manager`) to work correctly with a per-run instance rather
   than an instance attribute set once at construction time.
3. Add an automated regression test (e.g. `tests/test_orchestrator.py`)
   that calls `orchestrator.run()` twice with the same `profile_id` and
   tool input, using a stub tool that increments a call counter, and
   asserts the tool is executed twice (not cached across reviews).
4. Re-run `scripts/reproduce_43.py` to confirm the "BUG REPRODUCED" message
   no longer appears, and instead see `stub_tool.call_count == 2`.
5. Review whether within-review memoization (the original intended purpose
   of `ContextManager`, e.g. two tools in the same plan needing the same
   input) still works correctly after the fix — this behavior should be
   preserved, only cross-review caching should be removed.

### Inputs & outputs
Input: `Orchestrator.run(profile_id, profile_data)`, called once per review
request from the API layer.
Output: `run()` returns a dict of fresh `tool_results` for that specific
call reflecting the current `profile_data`, with no unintended reuse of
another call's cached results. Within a single `run()` call, if the exact
same tool+input pair is needed twice (legitimate memoization), it may still
be cached, but this must not survive between separate `run()` calls.

### Risks & unknowns
- Need to confirm whether `ContextManager` is used anywhere else in the
  codebase (e.g. directly by tools, or referenced outside `orchestrator.py`)
  that could break if its lifecycle changes — need to grep for
  `ContextManager` and `context_manager` usage across the repo before
  finalizing the fix.
- Need to confirm how `Orchestrator` is instantiated in the FastAPI app
  (single instance at startup vs. per-request) — this affects exactly how
  the fix should be implemented (e.g. per-run instantiation vs. a
  `reset()`/`clear()` call at the start of `run()`).
- Redis-backed `session_store` state (separate from `context_manager`) also
  persists per `profile_id` with a 1-hour TTL and is merged into
  `session_state` on each `run()` call via `session_state.update(results)`.
  Need to verify this doesn't reintroduce a related staleness issue even
  after the `ContextManager` fix — may need its own invalidation on
  portfolio update, or may be intentional (unclear yet, worth asking in
  Slack/office hours).

### Edge cases
- Two different users triggering reviews concurrently should not share or
  leak cached results between each other.
- A user requesting the same review twice in immediate succession with an
  *unchanged* portfolio (no update in between) — is fresh execution every
  time acceptable performance-wise, or should there be a legitimate
  short-lived cache for true no-change cases? Needs product/design input.
- Tools that fail (like the `market_analyzer` "Unknown tool" error seen in
  the reproduction) should not be cached as if they succeeded, and should
  be safely retried on the next review.
- Empty or missing `profile_data` fields (e.g. no `github_username`) should
  not break the plan-building or caching logic.