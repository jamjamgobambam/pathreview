# Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user
— https://github.com/ascherj/pathreview/issues/43

### Understand

The orchestrator caches per-profile "session state" in Redis (via
`agent/memory/session_store.py`). When a profile is reviewed a second time,
`Orchestrator.run()` loads the previous session and merges the new results onto
it with `dict.update()` — it never clears the old state:

```python
# agent/orchestrator.py
session_state = self.session_store.get(profile_id) or {}
...
session_state.update(results)          # merges onto stale data
self.session_store.set(profile_id, session_state)
```

- **Expected:** each review reflects only the tools that ran for the current
  portfolio. If the user removes their resume, the previous `skill_extractor`
  result should no longer be part of their session.
- **Actual:** results from tools that ran in a prior review persist forever,
  because `.update()` keeps any key that the new run does not overwrite. The
  user gets feedback based on data that no longer exists in their portfolio.

Confirmed by `tests/unit/test_orchestrator_session.py`, which runs two reviews
(with, then without a resume) and shows `skill_extractor` still present in the
session after the second review.

### Map

Files involved:
- `agent/orchestrator.py` — **primary fix site**; the load/merge/persist logic
  in `Orchestrator.run()` (roughly lines 46–67).
- `agent/memory/session_store.py` — already exposes an unused `delete()` method
  that can clear a session; no change strictly required but relevant.
- `tests/unit/test_orchestrator_session.py` — the reproduction test that will
  become the regression guard.

Out of scope for this issue:
- `core/services/review_service.py` — `_run_agent_orchestration()` is currently
  a hardcoded placeholder and does not call the orchestrator, so the bug is not
  reachable from the UI. Wiring the orchestrator into the request flow is a
  separate concern.

### Plan

1. In `Orchestrator.run()`, stop merging onto the previous session. Build the
   persisted state from only the current run's `results` (or call
   `self.session_store.delete(profile_id)` before `set`).
2. Document the intended "each review starts fresh" semantics in the
   `run()` docstring so the behaviour is explicit.
3. Remove the `xfail` marker from `test_removed_tool_not_persisted_across_reviews`
   so it becomes a passing regression test.
4. Add a companion test asserting that a tool which runs in both reviews has its
   result correctly overwritten with the newer value (not duplicated/stale).
5. Run the quality gates: `ruff check .`, `black --check .`, `mypy`, and
   `pytest tests/unit`.

### Inputs & outputs

- **Input:** `profile_id` (str) and the current `profile_data` (dict) for the
  review being run.
- **Output:** the persisted Redis session for `profile_id` contains exactly the
  tool results produced by the current review — no results from tools that did
  not run this time. The return value of `run()` is unchanged.

### Risks & unknowns

- **Intended persistence?** Unsure whether any consumer deliberately relies on
  session state carrying across separate reviews. Need to confirm the intent
  (issue text and `docs/adr/003-agent-orchestration.md`) before removing the
  merge.
- **ContextManager interaction.** `agent/memory/context_manager.py` provides
  in-memory memoization within a single orchestrator instance; need to make
  sure the session fix and the memoization cache don't mask each other.
- **Concurrency.** Two reviews for the same `profile_id` running concurrently
  could still race on the Redis key; clearing state may change that behaviour.
- **TTL semantics.** Sessions are stored with a 1-hour TTL; clearing vs.
  overwriting should not change the intended expiry behaviour.

### Edge cases

- First review for a profile (no prior session exists).
- A tool present in review 1 but absent in review 2 (the core bug).
- A tool that runs in both reviews (result should update to the new value).
- A tool that raises an error mid-review (partial results should not corrupt
  the session).
- An empty plan (no tools to run) — session should end up empty, not stale.
- The same tool called with different input between reviews.
- Redis temporarily unavailable — `run()` should still complete gracefully.
