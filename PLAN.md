## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user (Issue #43)](https://github.com/ascherj/pathreview/issues/43)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
- **Root Cause:** In `agent/orchestrator.py`, `Orchestrator.run()` keys Redis session storage by `profile_id` (`session_store.get(profile_id)` and `session_store.set(profile_id, session_state)`). Because a user's `profile_id` remains the same across multiple review requests, `Orchestrator.run()` loads the previous session state from Redis (`session_state = self.session_store.get(profile_id) or {}`), executes the new plan, and merges the new tool results into the loaded state (`session_state.update(results)`).
- **Expected Behavior:** Each review run should start with a clean session state (or session state scoped to a unique review/session ID), so tool results from prior reviews for the same user profile do not leak forward into subsequent reviews.
- **Actual Behavior:** Prior tool results (e.g. `github_tool` analysis from a previous review) persist in Redis under `session:profile_id` and bleed into future reviews when the user submits updated portfolio data.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

Files involved:
- `agent/orchestrator.py` — `Orchestrator.run()` method where session state retrieval, update, and persistence occur.
- `agent/memory/session_store.py` — `SessionStore` class for Redis session storage operations.
- `tests/unit/test_orchestrator.py` — Unit tests for orchestrator session state isolation and tool execution.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. **Option Selection & Signature Update:** Update `Orchestrator.run()` to accept an optional `session_id: Optional[str] = None` or `clear_session: bool = True` parameter (defaulting to scoping the Redis key to `session_id` if provided, or clearing previous state for `profile_id` at the start of a review execution).
2. **Session State Isolation in `Orchestrator.run()`:**
   - If scoping by `session_id`: build the session key from `session_id` (or fallback to `profile_id`) and start with a clean session dictionary for new review runs instead of accumulating across runs.
   - If scoping by review: ensure `session_store.set()` uses the isolated session key or clears old session keys before storing new run results.
3. **Verify and Update Tests:**
   - Run `tests/unit/test_orchestrator.py` and verify that `test_session_state_leakage_between_reviews` passes.
   - Add unit tests verifying custom `session_id` handling, Redis TTL preservation, and backward compatibility for callers not providing explicit session IDs.
4. **Code Quality and Cleanup:**
   - Run `ruff` linter and `black` formatter across modified agent files.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- **Inputs:** `Orchestrator.run(profile_id: str, profile_data: dict, session_id: Optional[str] = None)`
- **Outputs:** Dict returning `"profile_id"`, `"session_id"` (if provided), `"tool_results"`, and `"cached_results"`.
- **Change:** Redis key is scoped per review (`session:<session_id>`) or previous session state for the profile is cleared at run initialization, ensuring no stale state leakage between reviews.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- **Risks:** Callers of `Orchestrator.run()` throughout the API or review service might rely on positional or keyword arguments; adding `session_id` as an optional parameter maintains full backward compatibility.
- **Unknowns:** Whether existing downstream callers expect session state to persist *during* sub-steps of a single multi-stage review. Scoping to per-review `session_id` satisfies both multi-step within-review persistence and cross-review isolation.

### Edge cases
What inputs or states should your fix handle gracefully?
- `session_id` is `None`: Gracefully fall back to generating or using `profile_id` while ensuring session state is cleared before starting a new run.
- `session_store` is `None`: Function correctly without raising `AttributeError` when Redis is disabled/unavailable.
- Exceptional tool failures during a run: Ensure failed tools do not corrupt session state for subsequent clean runs.
