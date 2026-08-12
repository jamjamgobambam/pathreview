## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user — [#43](https://github.com/ascherj/pathreview/issues/43)

### Understand

**Expected behavior:** When a user updates their portfolio (e.g. adds/removes a resume, changes a README) and requests a new review, the orchestrator should reflect the current state of the portfolio — tool results should only include output computed from current data.

**Actual behavior:** `Orchestrator.run()` (`agent/orchestrator.py:31-76`) loads the previous run's `session_state` from Redis, executes only the tools relevant to the *current* profile data (via `_build_plan`), then merges the new results into the old state with `session_state.update(results)` (line 66) and saves the merged dict back.

`dict.update()` only adds/overwrites keys present in its argument — it never removes keys missing from it. So if a tool ran in a previous review but the input that triggered it is no longer present (e.g. resume deleted, so `skill_extractor` no longer appears in the plan), that tool's stale output is never dropped from `session_state`. It persists in Redis indefinitely (or until the 1-hour TTL expires), even though the data it was computed from no longer exists.

Root cause: `session_state.update(results)` is a non-destructive merge with no invalidation step. There is no code path anywhere in the repo that calls `SessionStore.delete()` — confirmed via repo-wide grep.

### Map

Files expected to be touched:
- `agent/orchestrator.py` — `run()` method (lines ~46-67), where session state is loaded, merged, and persisted. This is the primary fix location.
- `agent/memory/session_store.py` — `SessionStore.delete()` already exists (lines 68-81) but is unused; may need a small addition (e.g. a `replace()` method) depending on chosen approach.
- `tests/unit/test_orchestrator_session.py` — reproduction test already added; will extend with regression coverage for the fix.
- `JOURNAL.md` / `PLAN.md` — process docs, not code.

Not expected to change: `agent/memory/context_manager.py` (per-instance in-memory cache, already correctly scoped and not implicated), tool implementations under `agent/tools/`.

### Plan

1. Decide on invalidation strategy: replace `session_state` entirely with the current run's `results` each time, rather than merging old + new. This is the simplest fix and matches the expected behavior (session should reflect *current* portfolio state, not a running history).
2. Update `Orchestrator.run()` (`agent/orchestrator.py:64-67`) to persist `results` directly instead of `session_state.update(results)` — i.e. stop reading old state into the merge, or explicitly drop keys not present in the current `plan` before merging.
3. Confirm whether `session_state` (the value loaded from Redis) is used anywhere else in `run()` besides the merge/persist step — currently it's loaded but never read for anything other than the update-then-set (should double check callers don't rely on accumulation across runs, e.g. a partial-review-then-full-review flow).
4. Update/extend `tests/unit/test_orchestrator_session.py` so `test_removed_tool_output_does_not_linger_in_session` passes, and add a case confirming that when a tool's inputs are unchanged across runs, its previous output is still correctly available if intentionally desired (avoid regressing legitimate caching behavior, if any exists).
5. Run `make test-unit` and `make lint` / `make typecheck` to confirm no regressions elsewhere in the agent test suite.

### Inputs & outputs

**Input:** `profile_id` (str) and `profile_data` (dict) passed to `Orchestrator.run()`. `profile_data` shape varies per review — some fields (`resume_text`, `readme_content`, `files`, etc.) may be present in one call and absent in the next.

**Output:** The dict returned by `run()` (`tool_results`, `cached_results`) and, more importantly for this bug, the state persisted to Redis via `session_store.set()`. After the fix, the persisted state should reflect only tools executed in the current run — no leftover keys from a prior run's now-irrelevant data.

### Risks & unknowns

- Unclear whether `session_state` accumulation was originally intentional for some other use case (e.g. supporting partial/incremental reviews where old results are meant to be preserved until explicitly replaced). Need to check `agent/orchestrator.py` git blame / any related design notes before assuming a full replace is safe — a full replace could be *too* aggressive if some tool intentionally isn't re-run every time to save cost.
- `Orchestrator` and `SessionStore` are currently not wired into the live API (`core/services/review_service.py:282` is a stubbed placeholder) — the fix needs to work correctly once orchestration is actually connected, but there's no integration test coverage today, so a regression here might not surface until that wiring happens.
- No existing tests for `session_store.py` in isolation; changes there should get direct unit coverage too, not just orchestrator-level tests.

### Edge cases

- Profile updated to remove **all** tool-triggering fields (empty profile data) — session state should end up empty, not retain any prior results.
- Profile re-reviewed with **identical** data (no change) — should not error, and behavior should be well-defined (recompute vs. reuse — pick one deliberately rather than accidentally).
- First-ever review for a `profile_id` with no prior Redis entry — `session_store.get()` returns `None`, `session_state` defaults to `{}` (already handled at `agent/orchestrator.py:49`).
- Redis TTL expiring mid-flow (session already gone) — same as first-ever review case, already handled by `get()` returning `None`.
- A tool execution failure (`results[tool_name] = {"error": ..., "success": False}` at line 62) — confirm error results aren't persisted in a way that masks a previously successful result, or vice versa.
