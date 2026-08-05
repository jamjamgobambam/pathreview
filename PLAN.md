## Solution plan

**Issue:** [Orchestrator catches all exceptions from tool calls and continues without logging the failure (#44)](https://github.com/ascherj/pathreview/issues/44)

### Understand
`Orchestrator.run()` (`agent/orchestrator.py`) loops over a list of planned
`(tool_name, tool_input)` steps and executes each via `_execute_tool`, which
itself retries the tool up to 2 times through `retry_with_backoff`
(`agent/error_handling.py`) before re-raising. Back in `run()`, that
re-raised exception is caught by a bare `except Exception`, logged once more,
and converted into `results[tool_name] = {"error": str(e), "success": False}`
— then the loop just continues to the next tool.

**Expected behavior:** a tool failure (timeout, unknown-tool `ValueError`,
upstream API error, etc.) should be clearly distinguishable from a
successful result, and the overall run should communicate that it partially
or fully failed, so a caller building a review can react (e.g. mark that
section as unavailable, retry the whole review, or surface a warning to the
user) instead of silently treating the error stub as if it were tool data.

**Actual behavior (reproduced in `tests/unit/test_orchestrator.py` and
documented inline in `agent/orchestrator.py`):**
- `run()` never raises and never reports failure at the top level —
  `output.keys()` is always just `{"profile_id", "tool_results",
  "cached_results"}` regardless of how many tools failed.
- A failed tool's entry in `tool_results` has a completely different shape
  (`{"error": ..., "success": False}`) than a successful tool's entry
  (whatever `ToolResult.data` happens to contain for that tool), so nothing
  can tell the two apart without independently re-implementing that
  knowledge at every call site.
- `_build_plan()` unconditionally queues a `market_analyzer` step whenever
  any other tool ran, without checking it's registered in `self.tools` —
  so an incomplete `tools` dict (as in the real app today, where
  `Orchestrator` isn't wired into `core/services/review_service.py` yet)
  hits this same silent-failure path via `ValueError("Unknown tool: ...")`.

### Map
- `agent/orchestrator.py` — `Orchestrator.run()` (the swallow site) and
  `Orchestrator._build_plan()` (the unregistered-tool gap). Primary fix
  target.
- `agent/error_handling.py` — `retry_with_backoff` already logs and
  re-raises correctly; no change expected here, but worth confirming its
  behavior once `run()` changes (e.g. does it need a distinct exception type
  to distinguish "retries exhausted" from other errors?).
- `tests/unit/test_orchestrator.py` — new file (this week), will be updated
  to assert the *fixed* behavior instead of documenting the bug.
- `core/logging.py` / `api/main.py` — related gap found during
  reproduction: `configure_logging()` is only called from
  `scripts/seed_db.py`, never from `api/main.py`, so in the running server
  `Orchestrator`'s `structlog` calls use structlog's unconfigured defaults
  rather than the JSON/console renderer `core/logging.py` defines. Likely a
  small follow-up fix in `api/main.py`, in scope since the issue is
  fundamentally about "no indication that something went wrong."
- Possibly `core/services/review_service.py` — `_run_agent_orchestration`
  is currently a placeholder stub that doesn't call `Orchestrator` at all.
  Not planning to wire it up as part of this fix (out of scope for #44),
  but noting it so the new `tool_results` shape is designed to be easy to
  consume whenever that wiring happens.

### Plan
1. Define a consistent result shape for `tool_results` regardless of
   success/failure — e.g. always `{"success": bool, "data": dict | None,
   "error": str | None}` — so callers can check `.success` uniformly instead
   of guessing from key shape.
2. Add a run-level failure signal to `run()`'s return value, e.g.
   `"failed_tools": [...]` and/or `"status": "complete" | "partial" |
   "failed"`, computed from how many/which tools failed.
3. Fix `_build_plan()` to skip (or explicitly error on) tools not present in
   `self.tools` instead of queuing them and letting them fail at execution
   time with an opaque `ValueError`.
4. Wire `configure_logging()` into `api/main.py` startup so
   `Orchestrator`'s error logs are actually structured/visible in the
   running server, not just in standalone scripts.
5. Update `tests/unit/test_orchestrator.py` to assert the new shape/signal
   instead of the buggy behavior, and add a case for the `_build_plan`
   unregistered-tool fix.

### Inputs & outputs
- **Input:** unchanged — `Orchestrator(tools, session_store, tool_timeout)`
  and `run(profile_id, profile_data)`.
- **Output:** `run()` still returns a dict, but `tool_results[tool_name]`
  becomes a uniform shape, and the top-level dict gains a field(s)
  communicating partial/total failure so a caller doesn't have to inspect
  every entry to know something went wrong.

### Risks & unknowns
- Changing `tool_results`' shape is a breaking change for any future caller
  written against today's ad-hoc shape — but since `Orchestrator` isn't
  wired into the API yet (confirmed via grep), the blast radius today is
  limited to this module and its tests.
- Unsure whether the fix should make `run()` raise on total failure (fail
  loud) vs. always return a status dict (fail soft) — leaning toward
  fail-soft with a clear status field, since a single flaky tool shouldn't
  necessarily abort an entire multi-tool review, but this needs a second
  opinion from a mentor/instructor before committing to the API shape.
- `session_store.set()` is still called even when tools fail, meaning
  partial/error results get persisted as "session state" — need to decide
  if failed entries should be persisted as-is or filtered out before caching
  under `context_manager`/`session_store`.

### Edge cases
- All tools succeed (no regression).
- Every tool fails (run should not silently look identical to a full
  success).
- A tool that isn't registered in `self.tools` at all (the `market_analyzer`
  case) vs. a tool that's registered but raises at execution time — both
  should be reported the same way to the caller.
- A tool that times out (`TimeoutError`) vs. one that raises a normal
  exception — confirm both end up in the same uniform shape.
- `session_store` is `None` (no persistence) — failure reporting shouldn't
  depend on it being configured.
