## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user — [#43](https://github.com/ascherj/pathreview/issues/43)

### Understand
`Orchestrator.run()` (`agent/orchestrator.py:31-76`) keys the Redis-backed `SessionStore` by `profile_id`, which identifies a *user*, not a *review run*. On every call it does:

```python
session_state = self.session_store.get(profile_id) or {}
...
session_state.update(results)
self.session_store.set(profile_id, session_state)
```

`results` only contains entries for tools that were part of *this run's* plan (`_build_plan`, lines 78-134 — plan membership depends on which fields are present in `profile_data`, e.g. `files`, `readme_content`, `resume_text`). Because `session_state` starts as whatever was persisted from the previous review and is only ever added to, never cleared or replaced, any tool result from an earlier review that isn't re-produced by the current run's plan survives untouched in the persisted blob under the same `profile_id` key.

Expected behavior: each review reflects only the current run's inputs — either fresh tool results, or the explicit absence of a tool that no longer applies.
Actual behavior: the persisted session accumulates tool outputs across reviews indefinitely (each `set()` resets the 1-hour TTL, so it never naturally expires either), so a later review can return/persist stale data for a tool that didn't even run this time, or use unrelated leftover keys from a prior review of the same user.

Reproduced in `tests/unit/test_orchestrator_session_state.py`: a user's first review runs `github_tool` + `tech_detector`; their second review only supplies `github_tool` inputs, yet `tech_detector`'s stale result from the first review is still present in the persisted session state afterward.

### Map
- `agent/orchestrator.py` — `Orchestrator.run()` (session load/merge/persist, lines 46-49 and 64-67); `Orchestrator._build_plan()` (determines which tools run this request, lines 78-134). This is where the keying/merge logic needs to change.
- `agent/memory/session_store.py` — `SessionStore.get/set/delete` (Redis key is `session:{session_id}`, line 31/58/74). Needs a `session_id` that is unique per review, not per user, plus a way to still look up "the user's most recent review" if that's needed elsewhere.
- `agent/memory/context_manager.py` — in-memory `ContextManager`, scoped to a single `Orchestrator` instance already (recreated per request), so it is not the source of the cross-request bug, but its `hash_input`/cache-hit path needs to stay consistent with whatever new state model is used.
- Any caller that constructs `Orchestrator` and passes `profile_id` as the session key (need to grep the API/service layer, e.g. `agent/review_service.py` or similar, to find where `Orchestrator.run(profile_id, ...)` is invoked) — this is where a real per-review session id would need to be generated/passed in.
- `tests/unit/test_orchestrator_session_state.py` — new reproduction test to turn green once fixed.

### Plan
1. Introduce a per-review session identifier (e.g. `f"{profile_id}:{review_id}"` or a UUID minted per request) distinct from `profile_id`, and thread it through wherever `Orchestrator.run()` is called instead of reusing `profile_id` directly.
2. Change `Orchestrator.run()` to not merge stale state into fresh results: either (a) stop reading old `session_state` into the base dict entirely and only persist `results` for the current run, or (b) if some cross-run continuity is genuinely needed (e.g. resuming an in-progress multi-step review), scope that continuity explicitly by session id and only merge state that belongs to the same in-progress session, not the user's entire history.
3. Update `SessionStore` (or add a method) to support clearing/replacing a session's state on write rather than assuming callers always want an additive merge, so `set()` semantics match "this is the full current state," not "add to whatever was there."
4. Update/verify the caller(s) that invoke `Orchestrator.run()` to generate and pass a fresh session id per review request, and confirm nothing downstream depends on the old profile-id-keyed accumulation behavior (e.g. any UI reading "cached_results" across reviews).
5. Turn `tests/unit/test_orchestrator_session_state.py` green, and add a companion test asserting that within a single legitimate multi-step session (same session id, same review), intended state *is* still preserved — so the fix doesn't overcorrect into losing all continuity.

### Inputs & outputs
- Input: `Orchestrator.run(session_key, profile_data)` where `session_key` is now per-review rather than per-user; `profile_data` unchanged.
- Output: `run()`'s returned `tool_results` and the state persisted to Redis should only reflect tools actually executed in the current run (either freshly computed or legitimately cache-hit within the same session), with no leftover keys from unrelated prior reviews of the same user.

### Risks & unknowns
- Need to confirm whether any other part of the codebase (frontend, API routes) reads the Redis `session:{profile_id}` key expecting cumulative history across reviews — changing the keying scheme could silently break that consumer. Have to grep for `session_store.get(` call sites outside `orchestrator.py` before changing the key format.
- Unclear whether "session" in this product is meant to span multiple tool-calling turns within one review (where merging genuinely matters) — if so, the fix needs to preserve that intra-review merge behavior while still keying separate reviews (of the same user) apart. Getting this boundary wrong risks either losing needed continuity or reintroducing the same staleness bug in a narrower form.
- `SessionStore.set()` swallows all exceptions and only logs (`agent/memory/session_store.py:65-66`), so a failed write during the fix could fail silently in tests/dev without an obvious signal — worth tightening error visibility while touching this file.

### Edge cases
- First-ever review for a profile (no prior session state) — should behave the same as today (empty base state).
- A tool present in review N but absent in review N+1 (reproduced by the test) — must not leak into N+1's results/state.
- Two reviews for the same user firing concurrently (e.g. duplicate submit) — the new session id scheme must not let one overwrite the other's Redis key mid-flight.
- A tool that legitimately should be cache-hit within one session (same session id, same input hash) — must still work via `ContextManager`, unaffected by the `SessionStore` keying fix.
