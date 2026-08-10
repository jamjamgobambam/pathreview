## Solution plan

**Issue:**
- Agent session state is not cleared between reviews for the same user #43
- https://github.com/ascherj/pathreview/issues/43

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

- **Root cause — two caching layers, both scoped to the wrong lifetime:**
  1. **SessionStore (Redis, persists across calls):** `Orchestrator.run()` loads the prior review's state (`agent/orchestrator.py:49`) and *merges* the new run's results on top (`:66`, `session_state.update(results)`) before writing it back (`:67`). Tool results from an earlier review that aren't recomputed this run survive under `session:<profile_id>` (1-hour TTL).
  2. **ContextManager (in-memory, per Orchestrator instance):** created once in `__init__` (`:29`) instead of per `run()`, even though it is documented as "within-session" memoization. On a reused Orchestrator instance, `cached_results` (`:75`) accumulates every prior review's results, and `market_analyzer`'s constant input `{"detected_skills": {}}` (`:130`) produces an identical hash every run, so the cache check (`:150–155`) returns the previous review's result without recomputing.
- **Expected behavior:** each review reflects only the current submission across *both* layers.
- **Actual behavior:** a README-only review's `readme_scorer` still appears for a later resume-only review of the same `profile_id` (proven by `scripts/reproduce_issue_43.py`); `cached_results` grows across reviews; and `market_analyzer` keeps returning the first review's answer.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `agent/orchestrator.py` — `Orchestrator.__init__` (`:29`), `run()` (state load `:47–49`, merge `:66`, persist `:67`, `cached_results` `:75`), and `_execute_tool`'s cache path (`:150–155`). **Primary edit.**
- `agent/memory/session_store.py` — `get / set / delete`. The `delete(session_id)` method (`:68`) already exists but is **never called**; the fix activates it. Key format `session:<session_id>`, TTL 3600s.
- `agent/memory/context_manager.py` — no `clear()`/`reset()` method exists (only `store_tool_result / get_tool_result / get_all_results / hash_input`); reset by recreating the instance per `run()`.
- `tests/unit/test_orchestrator.py` — **new** regression test covering both layers.
- `tests/unit/test_session_store.py` — **new** (optional), `get/set/delete` round-trip.
- `scripts/reproduce_issue_43.py` — existing reproduction; assertions flip to "bug fixed" once the code lands.
- *Context only (not edited):* `core/services/review_service.py::_run_agent_orchestration` (a placeholder that never calls `Orchestrator`).

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Layer 1 — SessionStore:** in `run()`, remove the prior-state load (`:47–49`) and the `session_state.update(results)` merge (`:66`); then call `self.session_store.delete(profile_id)` followed by `self.session_store.set(profile_id, results)`. Keep the `if self.session_store:` guard.
2. **Layer 2 — ContextManager:** at the top of `run()`, recreate `self.context_manager = ContextManager()` so each review starts with a fresh within-session cache — fixing both the `cached_results` accumulation and the `market_analyzer` constant-hash stale hit.
3. **Regression test** `tests/unit/test_orchestrator.py`: run two consecutive reviews on a *single* Orchestrator instance (README-only, then resume-only) against a `Mock`-backed `SessionStore`, and assert (a) the persisted Redis payload has no `readme_scorer`, (b) run 2's `cached_results` has no `readme_scorer`, and (c) `market_analyzer` recomputes in run 2 instead of returning run 1's value. Mirror the Mock-redis pattern in `tests/unit/test_rate_limiter.py`; mark `@pytest.mark.unit`.
4. *(Optional)* Add `tests/unit/test_session_store.py` covering `get/set/delete` and confirming `delete()` removes the key.
5. Run `make lint`, `make typecheck`, and `make test-unit`; update `scripts/reproduce_issue_43.py` so its assertions flip from "bug present" to "bug fixed" for both layers.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input (unchanged):** `run(profile_id: str, profile_data: dict)`.
- **Output (same shape):** the return dict `{ "profile_id", "tool_results", "cached_results" }` — but `tool_results["market_analyzer"]` now reflects the current review, and `cached_results` contains only the current run's results.
- **Behavior change:** what is persisted under `session:<profile_id>` becomes exactly the current run's `results` (no merge with prior state); `SessionStore.delete()` goes from unused → called once per run; the `ContextManager` is reset each `run()`. No new parameters are introduced (a per-review `session_id`/`review_id` parameter is the deferred alternative noted below).

### Risks & unknowns
What could go wrong? What are you still unsure about?

- **Alternative considered — unique per-review `session_id`:** namespace each review with a uuid/`review_id`-scoped key. Rejected for this Tier-1 fix because it adds a `run()` parameter with **no production caller** (only `scripts/reproduce_issue_43.py` calls `run`) and sprays orphaned Redis keys (each with a 1-hour TTL) that would themselves need cleanup. Kept as the fallback if per-review accumulation is ever required.
- **Instantiation lifetime unknown:** production doesn't wire `Orchestrator` in yet (`core/services/review_service.py::_run_agent_orchestration` is a placeholder). The fix is **defensive** — correct whether the eventual wiring creates one Orchestrator per review or reuses a long-lived one. Investigation path: confirm the intended lifetime when the wiring lands.
- **Separate gap (out of scope):** `market_analyzer` receives empty `{"detected_skills": {}}` (`agent/orchestrator.py:130`, "Will be populated by context"). Resetting the cache fixes the *staleness* but not the empty input — a distinct feature gap, flagged not fixed.
- **Redis-error path:** `SessionStore.delete/set` swallow exceptions and log; need to confirm `run()` still returns without raising when Redis errors.
- **Semantic risk:** no caller relies on cross-run accumulation (a repo-wide grep for `Orchestrator` matches only `agent/orchestrator.py` and the repro script).

### Edge cases
What inputs or states should your fix handle gracefully?

1. **First-ever review** for a profile: `get()` returns `None` and `delete()` on a missing key must be a safe no-op.
2. **Reused Orchestrator, different tool sets** (README-only → resume-only): run 2 must not surface `readme_scorer` in Redis **or** in `cached_results`.
3. **`market_analyzer` constant input across reviews:** must recompute per review, not serve the cached prior-run result.
4. **`session_store is None`** (allowed by the optional constructor param): the persist/delete block stays guarded by `if self.session_store:`, and the ContextManager reset still runs (independent of `session_store`).
5. **Redis raises** during `delete`/`set`: `run()` still returns its result dict with no unhandled exception.
6. **Empty plan / empty `profile_data`:** `results` is `{}`; persisting must empty the stored state (and leave `cached_results` empty) rather than retain stale keys.
