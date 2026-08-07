## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user](https://github.com/ascherj/pathreview/issues/43)

### Understand

`Orchestrator` creates one `ContextManager` in `agent/orchestrator.py` and reuses it
across every call to `run()`. Because `_execute_tool()` checks that shared context
before calling a tool, a later review can reuse a result cached during an earlier
review. The reproduction makes this visible with `market_analyzer`, whose plan input
is currently the same empty `detected_skills` dictionary on both runs: the second
review reports the first execution's result and never calls the tool again.

There is a second stale-state path in the Redis-backed session data. `run()` loads
the dictionary stored under the profile ID, merges the current results into that
dictionary, and writes it back. If the updated portfolio no longer schedules a tool,
that tool's result from the earlier review remains in the persisted session.

The expected behavior is for each new review to begin with fresh in-memory and
persisted tool state, while still allowing memoization among repeated tool calls
inside that one review. The actual behavior lets results outlive the review that
created them.

### Map

- `agent/orchestrator.py`
  - `Orchestrator.__init__()` creates the long-lived `ContextManager`.
  - `Orchestrator.run()` loads and merges stored state by `profile_id`.
  - `Orchestrator._execute_tool()` reads and writes the long-lived memoization cache.
- `agent/memory/context_manager.py`
  - `ContextManager.results` owns the in-memory tool-result cache and currently has
    no review boundary or reset operation.
- `agent/memory/session_store.py`
  - `SessionStore.get()`, `set()`, and `delete()` operate on the
    `session:{profile_id}` Redis key. The store already supports replacement and
    deletion, but the orchestrator currently supplies a merged historical value.
- `tests/unit/test_orchestrator_session_isolation.py`
  - Contains the failing reproduction and will become the regression suite for
    sequential review isolation.

Expected implementation files: `agent/orchestrator.py`,
`agent/memory/context_manager.py`, and
`tests/unit/test_orchestrator_session_isolation.py`. I will change
`agent/memory/session_store.py` only if the implementation needs an explicit
replace/clear contract that cannot be expressed safely with its existing methods.

### Plan

1. Give each `Orchestrator.run()` call its own `ContextManager`, and pass that
   review-local context through tool execution so memoization still works within a
   review without leaking across reviews.
2. Stop loading and merging the previous profile session when a new review begins.
   Persist only the current review's `results` so tools omitted from the new plan are
   removed from Redis state.
3. Keep the no-Redis path working and make Redis cleanup/replacement failures
   observable without allowing old in-memory results to be reused.
4. Update the reproduction tests to verify fresh execution, replacement of stored
   state, isolation between different profiles, empty plans, and preservation of
   same-review memoization; then run the focused tests and the broader unit suite.

### Inputs & outputs

The fix takes the existing `profile_id`, `profile_data`, tool registry, and optional
`SessionStore` passed to `Orchestrator.run()`. No API request or response schema
should change.

For each call, the orchestrator should produce `tool_results` and `cached_results`
derived only from that call's execution plan and inputs. Redis should contain only
that review's current tool results under the profile session key. A second review
must invoke its relevant tools again even when a tool receives the same hashed input
as it did during the first review.

### Risks & unknowns

- Moving cache ownership in `agent/orchestrator.py` could accidentally disable useful
  memoization inside a single review. A test must call the same tool twice within one
  run and confirm that only the duplicate call is cached.
- Resetting a shared `self.context_manager` at the start of `run()` would be unsafe
  if one `Orchestrator` instance handles concurrent reviews. A review-local context
  avoids that race, but I still need to confirm how orchestrators are instantiated
  in the eventual API integration.
- `SessionStore` currently catches and logs Redis errors rather than surfacing them.
  The fix must not treat a failed `delete()` as proof that old state is gone; writing
  the current results as a replacement is safer than relying on deletion alone.
- `market_analyzer` currently receives an empty `detected_skills` input instead of
  prior tool output. That data-flow issue makes the cache bug easy to reproduce but
  is outside issue #43; the session-isolation fix should not expand into redesigning
  agent tool dependencies.
- The production review service currently contains a placeholder
  `_run_agent_orchestration()` implementation, so the regression belongs at the
  orchestrator unit boundary until the API is wired to the real agent.

### Edge cases

- Two consecutive reviews for the same profile have identical inputs: tools should
  still rerun because they belong to distinct reviews.
- The second review removes a source, so a previously scheduled tool is absent: its
  old result must not remain in persisted or returned state.
- A review has an empty execution plan: returned caches and persisted current state
  should be empty rather than preserving the prior review.
- No `SessionStore` is configured: review-local in-memory isolation must still work.
- Redis `get`, `delete`, or `set` fails: the current review should not fall back to
  an earlier review's in-memory result.
- Different profiles are reviewed sequentially or concurrently by one orchestrator:
  neither profile may see the other's cached tool results.
- A tool fails during the second review: the current error result should replace any
  older successful result for that tool instead of merging with it.
