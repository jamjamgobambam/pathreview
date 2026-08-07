## Solution plan

**Issue:** [#47 — Agent state isn't persisted across API restarts, causing in-progress reviews to be lost](https://github.com/ascherj/pathreview/issues/47)

### Understand

**Expected:** A review that spans multiple tool executions (5+ repos) survives an API process restart — work already completed before the restart is not redone.

**Actual:** `Orchestrator.run()` (`agent/orchestrator.py`) loads `session_state` from Redis at the start, executes every step in the plan in a `for` loop, and calls `self.session_store.set(profile_id, session_state)` exactly **once, after the loop finishes** (~line 67). Intermediate `results` live only in a local Python dict, and `ContextManager.results` (`agent/memory/context_manager.py`) is a plain in-memory `dict` by design — neither is ever written to Redis mid-run. If the process dies between tool 1 and tool N, nothing was persisted, and the loaded `session_state` (even though fetched) is never consulted to skip work — it's write-only. The review restarts from scratch.

Root cause: **persistence timing** (only at the very end) combined with **resume logic never implemented** (loaded state is discarded/overwritten, not used to skip completed tools).

### Map

- `agent/orchestrator.py` — `Orchestrator.run()`, `_execute_tool()`: primary fix location. Move persistence inside the loop; add resume-skip logic using the already-loaded `session_state`.
- `agent/memory/session_store.py` — no change expected; `get`/`set`/`delete` against Redis already work correctly and are reused as-is.
- `agent/memory/context_manager.py` — no change expected; it's intentionally in-session/in-memory (memoization within a single run), separate concern from cross-restart persistence.
- `tests/unit/test_orchestrator.py` — already contains the reproduction (`test_partial_progress_survives_a_mid_review_restart`, currently `xfail`). Will flip to a passing regression test once fixed, plus new tests for resume-skip behavior.

### Plan

1. **Persist incrementally**: inside the `for tool_name, tool_input in plan:` loop, call `self.session_store.set(profile_id, session_state)` after each tool's result is recorded (success or error), not just once after the loop.
2. **Use loaded state to resume**: before executing each planned tool, check if `session_state` already has a result for it; if so, skip execution and reuse the stored result instead of recomputing.
3. **Only skip successful results**: results stored as `{"error": ..., "success": False}` must still be retried on resume — don't let a failed tool block forever.
4. **Flip the reproduction test to green** and add a companion test that resumes a partially-completed session and asserts skipped tools aren't re-executed (e.g. via a call counter on a fake tool).
5. **Update `JOURNAL.md`/docstrings** to note the incremental-persistence + resume behavior, since `run()`'s current docstring doesn't mention resume semantics at all.

### Inputs & outputs

- **Input:** unchanged signature — `run(profile_id, profile_data)`. The difference is that an existing `session_state` in Redis for `profile_id` is now actually read and acted on (skip already-done tools) rather than just loaded and overwritten.
- **Output:** unchanged return shape (`{"profile_id", "tool_results", "cached_results"}`). Side effect changes: multiple smaller `session_store.set()` writes to Redis during a run instead of one write at the end; a resumed run does fewer tool executions than a fresh run covering the same plan.

### Risks & unknowns

- **Write volume**: N Redis writes per run instead of 1 — fine at current scale, but worth a quick gut-check if plans grow much larger.
- **TTL resets**: each `set()` refreshes the 3600s TTL (`session_store.py:56`). Probably desirable (keeps long reviews alive) but should be a deliberate choice, not incidental.
- **Skip-key correctness**: `session_state` is currently keyed by `tool_name` only, while `ContextManager` keys by `tool_name:input_hash`. If `profile_data` changes between the crash and the resume (e.g. a project added), a stale result keyed only by `tool_name` could be wrongly reused. Need to decide whether resume-skip should also hash inputs.
- **Concurrent resumes**: no locking in `SessionStore` — two workers picking up the same `profile_id` after a restart could race. Out of scope for this fix, but worth flagging rather than silently ignoring.
- **Plan drift**: if a deploy changes `_build_plan()` (new/renamed tool) between the original run and the resume, old `session_state` simply won't match new plan step names — should degrade gracefully (treated as "not yet done"), needs a test to confirm.

### Edge cases

- No `session_store` configured (`None`) — must keep working exactly as before (in-memory only, no crash).
- Empty plan (no tools to run) — `run()` should still return cleanly regardless of what's in `session_state`.
- Resume where **all** tools already succeeded — `run()` should skip everything and return the cached results without re-executing any tool.
- Resume where a previous attempt recorded an **error** for a tool — that tool must re-execute, not be treated as done.
- Redis unreachable mid-run (`session_store.set()`/`get()` raising) — `SessionStore` already catches and logs internally (`session_store.py:46-48,65-66`), so `run()` should keep proceeding in-memory-only for that run rather than crashing.
