# Solution plan

**Issue:** [Agent state isn't persisted across API restarts, causing in-progress reviews to be lost (#47)](https://github.com/ascherj/pathreview/issues/47)

### Understand

`Orchestrator.run()` (`agent/orchestrator.py`) loaded prior session state
from Redis at the top of the method (pre-fix line 47:
`session_state = self.session_store.get(profile_id) or {}`), but the tool
loop right below it never read from that dict — it called every tool in
`plan` unconditionally. The merged results were only written back to Redis
once, *after* the loop finished (pre-fix lines 64–66:
`session_state.update(results); self.session_store.set(...)`), not inside
it. So there were two independent bugs, not one:

1. Nothing was persisted until the whole plan finished, so a crash
   mid-review had nothing checkpointed to resume from.
2. Even on a run where a prior checkpoint *did* exist, the loop had no
   logic to consult it — every tool re-executed regardless of `results`.

**Root cause:** missing per-tool "already done" check in the loop body,
combined with a checkpoint write placed after the loop instead of inside it.

**Expected behavior:** a restart mid-review resumes — completed tools are
skipped, only unfinished/failed tools re-execute.
**Actual (pre-fix) behavior:** a restart always re-runs the entire plan from
scratch, confirmed in reproduction (see `JOURNAL.md`, Week 8): 3 of 4
regression tests fail when `agent/orchestrator.py` is reverted to
`cb5cc09^`.

### Map

Files touched (current, post-fix line numbers):

- `agent/orchestrator.py`
  - `run()`, line 33 — loop that now checks `results.get(tool_name)` per
    tool (lines 56–60: `already_done` check) before executing, and
    persists after every tool instead of once (lines 76–77:
    `self.session_store.set(profile_id, results)` moved inside the loop).
  - `_build_plan()` (line 87), `_execute_tool()` (line 142),
    `_execute_with_timeout()` (line 181) — unchanged in behavior, only
    reformatted/retyped (see below).
- `agent/memory/session_store.py` — `get()` (line 22) / `set()` (line 50):
  no behavior change, but `run()`'s per-tool check depends on `get()`'s
  `dict | None` contract, and `set()`'s `ttl_seconds=3600` default
  (line 50) bounds how long a checkpoint survives (see Risks below).
- `agent/memory/context_manager.py`, `agent/error_handling.py` — missing
  type annotations here blocked the mypy pre-commit hook on any change to
  `orchestrator.py` (which imports both), so both needed annotation fixes
  before the real change could be committed.
- `tests/unit/test_orchestrator.py` (new file, 180 lines) — four tests in
  `TestOrchestratorCheckpointing` (lines 57–180+):
  `test_progress_is_checkpointed_after_each_tool_not_only_at_the_end` (64),
  `test_restart_mid_review_resumes_without_rerunning_completed_tools` (88),
  `test_previously_failed_tool_is_retried_on_resume` (133),
  `test_no_session_store_runs_without_persistence` (164).

### Plan

1. Read `agent/orchestrator.py` end-to-end and confirm exactly where
   `session_state` was loaded vs. where it was (not) consulted, and where
   the single end-of-loop `session_store.set()` call sat.
2. Read `agent/memory/session_store.py` to confirm `get()`/`set()`'s
   contract (`dict | None`, JSON round-trip, TTL) so the per-tool check in
   `run()` matches what's actually stored (a `tool_name -> result` dict, not
   some wrapper object).
3. In `run()`, replace the unconditional loop with one that checks
   `previous = results.get(tool_name)` first; treat `previous is not None`
   and not `{"success": False}` as done → `continue`; otherwise execute and
   immediately call `self.session_store.set(profile_id, results)` before
   moving to the next tool (not after the loop).
4. Write regression tests that simulate a restart: run one `Orchestrator`
   through a partial plan, build a second `Orchestrator` sharing the same
   `session_store`, run it against the full plan, and assert
   `tool.execute.call_count` for the already-completed tools stays at 1
   (not re-invoked) while the remaining tool(s) do execute. Include a
   variant seeding a failed tool result to confirm it's retried, not
   skipped, and a variant with `session_store=None` to confirm unchanged
   no-persistence behavior.
5. Fix the missing annotations in `error_handling.py`, `context_manager.py`,
   `session_store.py` so `pre-commit` (mypy) passes on the changed files.
6. Run `pytest tests/unit/test_orchestrator.py -q` before and after the
   change (before: expect failures on the new tests against old behavior;
   after: all pass) — this is the same command used for reproduction in
   `JOURNAL.md`.

### Inputs & outputs

**Function changed:** `Orchestrator.run(profile_id: str, profile_data: dict) -> dict`

**Existing happy path (no restart):** input a `profile_data` dict with no
prior session state → every tool in `_build_plan()`'s plan executes once,
output is `{"profile_id", "tool_results", "cached_results"}` as before.

**New behavior (resume after restart):**
- Input: same `profile_id`, and a `session_store` whose `get(profile_id)`
  returns a dict where some tool names already have successful results.
- Expected output: `run()` returns the same shape, but
  `tool.execute.call_count == 0` for every tool already present with a
  successful result, and `== 1` for tools that were missing or previously
  failed.

**Test drafted (already implemented, `tests/unit/test_orchestrator.py:88`):**

```python
def test_restart_mid_review_resumes_without_rerunning_completed_tools(
    self, session_store: FakeSessionStore
) -> None:
    tools = {
        "tool_a": make_tool("tool_a", result={"result": "a"}),
        "tool_b": make_tool("tool_b", result={"result": "b"}),
        "tool_c": make_tool("tool_c", result={"result": "c"}),
    }
    full_plan = [("tool_a", {}), ("tool_b", {}), ("tool_c", {})]

    # First "process": stops after tool_a and tool_b (simulated restart).
    before = Orchestrator(tools, session_store=session_store)
    with patch.object(before, "_build_plan", return_value=full_plan[:2]):
        before.run("profile-1", {})

    # "Restart": fresh Orchestrator, same session_store, full plan.
    after = Orchestrator(tools, session_store=session_store)
    with patch.object(after, "_build_plan", return_value=full_plan):
        after.run("profile-1", {})

    assert tools["tool_a"].execute.call_count == 1  # not re-run
    assert tools["tool_b"].execute.call_count == 1  # not re-run
    assert tools["tool_c"].execute.call_count == 1  # runs for the first time
```

### Risks & unknowns

1. **JSON-serializability of tool results.** `SessionStore.set()`
   (`agent/memory/session_store.py:61`) does `json.dumps(data)` inside a
   bare `try/except Exception` that only logs on failure
   (lines 65–66) — a tool that ever returns something non-JSON-serializable
   (e.g. a `datetime`) would silently fail to checkpoint, with no visible
   error to the caller. Not an issue for current tools; worth a comment if
   a new tool is added later.
2. **"Done" is inferred from dict shape**, not an explicit status field:
   `previous is not None and not (isinstance(previous, dict) and
   previous.get("success") is False)` (orchestrator.py:57–59). A tool
   returning a truthy dict without a `success` key on partial failure would
   be misread as complete. Confirmed this isn't currently possible by
   checking `_execute_tool` (line 142) — failures always produce
   `{"error": ..., "success": False}` — but it's a convention, not an
   enforced contract.
3. **Fixed 3600s TTL** (`session_store.py:50` default `ttl_seconds=3600`).
   A review interrupted for longer than an hour loses its checkpoint
   entirely and a "resume" silently becomes a full re-run. The fix doesn't
   address this; flagging it as a known limitation rather than solving it,
   since making TTL dynamic is out of scope for #47.
4. **No coverage for two `Orchestrator` instances hitting the same
   `profile_id` concurrently** (a race on the Redis key). Not reachable in
   the current single-worker deployment, but would need a lock or
   optimistic-concurrency check if that changes.

### Edge cases

- All tools in the plan already have successful results in `session_store`
  → `run()` executes nothing new, returns cached results
  (covered by `test_restart_mid_review_resumes_without_rerunning_completed_tools`).
- A tool previously recorded `{"success": False, ...}` → retried, not
  skipped (covered by `test_previously_failed_tool_is_retried_on_resume`).
- `session_store=None` (persistence not configured) → identical to
  pre-fix behavior: every tool executes, nothing is checkpointed, no
  exception (covered by `test_no_session_store_runs_without_persistence`).
- `profile_data` changes between the interrupted run and the resume (e.g. a
  project's `github_repo` changes) so `_build_plan()` produces a tool name
  absent from the old `results` dict → `results.get(tool_name)` returns
  `None`, tool executes normally, not silently dropped.
- Redis returns corrupted/non-JSON data on `get()` → already handled by
  `SessionStore.get()`'s `except json.JSONDecodeError: return None`
  (session_store.py:43–45), so `run()` falls back to treating it as no
  prior state rather than crashing.
