## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user](https://github.com/ascherj/pathreview/issues/43)

### Understand
**Expected:** Each portfolio review starts with a clean agent session. Tools re-run against the current profile data so results reflect updates (new repos, README, resume, etc.).

**Actual:** Two layers keep stale data across reviews for the same profile:
1. `ContextManager` on `Orchestrator` is created once in `__init__` and memoizes tool results by `tool_name + sha256(input)` for the orchestrator’s lifetime. A second `run()` with the same tool inputs returns a cache hit and never re-executes the tool (`tool_result_cache_hit`).
2. `Orchestrator.run()` loads prior Redis session state via `SessionStore.get(profile_id)`, then does `session_state.update(results)` before `set()`. Old tool keys that are no longer in the plan remain in Redis. `SessionStore.delete()` already exists but is never called.

**Root cause:** Cross-review caching/merge instead of per-review isolation. In-request memoization (same tool/input twice inside one `run()`) is fine; cross-run reuse is not.

### Map
Files / symbols involved:
- `agent/orchestrator.py` — `Orchestrator.run()`, `_execute_tool()` (cache lookup)
- `agent/memory/context_manager.py` — `ContextManager` result dict; needs a `clear()` (or equivalent reset)
- `agent/memory/session_store.py` — `get` / `set` / `delete` (delete already implemented)
- `tests/unit/test_orchestrator_session_state.py` — reproduction tests (Week 8); will become regression tests after the fix

### Plan
1. Add `ContextManager.clear()` to wipe in-memory tool-result memoization.
2. At the start of `Orchestrator.run()`, clear the context manager and call `session_store.delete(profile_id)` when a store is configured — before building/executing the plan.
3. Stop merging old session state: persist only the current run’s `results` (replace `session_state.update(results)` with writing `results` alone).
4. Update `tests/unit/test_orchestrator_session_state.py` so the second review must re-execute tools and must not retain stale Redis keys; keep a test that same-input memoization still works *within* a single `run()` if needed.
5. Run `make test-unit` (and `make check` before the PR) to confirm no regressions.

### Inputs & outputs
**Inputs:** `profile_id: str`, `profile_data: dict` into `Orchestrator.run()`; optional `SessionStore` backed by Redis.

**Outputs / behavior change:**
- Each `run()` produces fresh `tool_results` from live tool execution (unless memoized within that same run).
- Redis session key `session:{profile_id}` holds only the latest run’s results (or is rewritten cleanly each time).
- Logs should show tools executing on the second review rather than only `tool_result_cache_hit`.

### Risks & unknowns
- **Shared Orchestrator lifetime:** If one orchestrator instance serves many users/profiles, clearing context at the start of *every* `run()` is required so profile A’s cache cannot leak into profile B’s same hashed inputs. Need to confirm how the API constructs Orchestrator (singleton vs per-request) before relying on instance isolation alone.
- **Intentional within-run memoization:** Clearing too late (or clearing mid-plan) could break duplicate tool steps in one plan. Clear only at the beginning of `run()`.
- **Redis failures:** `delete()` already swallows errors and logs; clearing should remain best-effort so a Redis blip doesn’t abort the review.
- **Other callers of SessionStore:** Grep shows only the orchestrator uses it today; still verify nothing else depends on accumulating session history across reviews.

### Edge cases
- Second review with **identical** `profile_data` (same hashed tool inputs) — must still re-execute tools after the fix.
- Second review with **changed** portfolio fields but some tools unchanged — must not keep removed tools’ old Redis entries.
- Review with **empty plan** (no github/files/readme/resume) — should still clear prior session rather than leave leftovers.
- `session_store=None` — clear path must no-op safely; only context manager clears.
- Tool **errors** on the second run — should store error payloads for this run only, not resurrect success payloads from the previous run.
- Concurrent reviews for the **same** `profile_id` — last writer wins in Redis; document as acceptable for Tier 1 / current design unless we find locking already elsewhere.
