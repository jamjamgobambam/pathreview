## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user — https://github.com/ascherj/pathreview/issues/43

### Understand
Root cause: `Orchestrator.run()` treats each review as an incremental update of the previous one instead of a fresh analysis. It loads the previous state (`session_state = self.session_store.get(profile_id) or {}`), runs only the tools in the current review's plan, then merges new results over old before persisting (`session_state.update(results)`). Because state is keyed by `profile_id` (the user) and reused, any tool that ran in an earlier review but is not in the current plan keeps its stale result in Redis.

- **Expected:** a new review starts fresh — the stored session reflects only the current review's tools, and removed/changed portfolio data is no longer present.
- **Actual:** stale tool results (e.g. `github_tool` for a removed project) persist across reviews, so updates to a user's portfolio are not fully reflected.

A second latent contributor: the `ContextManager` memoization cache in `_execute_tool`. It is fresh per `Orchestrator` instance, so it only leaks stale results if the same `Orchestrator` object is reused across reviews — depends on how the API layer instantiates it (open question).

### Map
Files expected to touch:
- `agent/orchestrator.py` — `run()`: stop merging prior state; clear/replace state per review. Possibly reset `context_manager` at the start of `run()`.
- `agent/memory/session_store.py` — reuse existing `delete()` / `set()`; no change likely needed, but verify.
- `tests/unit/test_orchestrator.py` — add a regression test for the two-review scenario.

To investigate (may or may not touch):
- `api/` layer where `Orchestrator` / `SessionStore` are instantiated — confirm whether an `Orchestrator` instance (and its `ContextManager`) is reused across requests.

### Plan
1. **Confirm instantiation** — trace where `Orchestrator` and `SessionStore` are created in the API layer to decide if the `ContextManager` reuse path is also live.
2. **Fix state handling in `run()`** — treat each review as fresh: do not load-and-merge previous `session_state`; persist only the current review's `results` (overwrite). Reset `self.context_manager` at the start of `run()` so in-session memoization can't carry across reviews.
3. **Add regression test** — reproduce the two-review scenario (project present → removed) and assert no stale keys remain in the stored session and that returned results reflect only the current plan.
4. **Run checks** — `make test-unit` and `make check` (lint/format/typecheck).
5. **Document** — update JOURNAL.md Week 8 with the reproduction commit link and PLAN.md link.

### Inputs & outputs
- **Input:** `profile_id: str` and `profile_data: dict` (github_username, projects, readme_content, resume_text, files, etc.).
- **Output/change:** `run()` returns `{profile_id, tool_results, cached_results}` reflecting only the current review; the persisted Redis session (`session:{profile_id}`) contains only the current review's tool results, with no leftover keys from prior reviews.

### Risks & unknowns
- If any consumer intentionally relies on cross-review accumulation of session state, overwriting would change that behavior — need to confirm no such consumer exists.
- Unknown whether the API reuses a single `Orchestrator` instance; if so, the `ContextManager` reset is required, not optional.
- Redis TTL (1 hour) means stale state also self-expires eventually — the fix must not rely on that.

### Edge cases
- First review for a user (no prior session state) — should behave normally.
- Review where the plan is empty (no applicable data) — stored state should be empty, not stale.
- A tool fails in the current review — its error result should replace, not sit alongside, a prior success.
- `session_store` is `None` (optional) — must still work without persistence.
- Same input across two reviews — should re-run (fresh) rather than serve a stale cached result.
