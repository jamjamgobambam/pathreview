## Solution plan

**Issue:** [Orchestrator catches all exceptions from tool calls and continues without logging the failure](https://github.com/ascherj/pathreview/issues/44)

### Understand

**Confirmed root cause.** `Orchestrator.run()` (`agent/orchestrator.py`, lines
51-62) calls `self._execute_tool(tool_name, tool_input)`, gets back a
`ToolResult` object, and does:

```python
result = self._execute_tool(tool_name, tool_input)
results[tool_name] = result.data if hasattr(result, 'data') else result
logger.info("tool_executed", tool=tool_name, success=True)
```

It never inspects `result.success` or `result.error`. Every tool in
`agent/tools/` (`github_tool.py`, `tech_detector.py`, `readme_scorer.py`,
`skill_extractor.py`, `market_analyzer.py`) already catches its own
exceptions internally inside `execute()` and always returns a `ToolResult`
(`success=True` or `success=False`) instead of letting an exception escape
(confirmed by reading all five `execute()` implementations). This means the
orchestrator's own `except Exception` blocks (lines 60-62 in `run()`, 171-173
in `_execute_tool()`) are effectively unreachable for real tool failures --
the only exception that reliably reaches them today is the explicit
`raise ValueError(f"Unknown tool: {tool_name}")` in `_execute_tool()` for an
unregistered tool name, which is a different, already-correctly-logged
scenario.

**Expected behavior:** when a tool reports failure (`ToolResult.success is
False`), the orchestrator should log the failure at error level with the
tool name and error message, and store something in `results[tool_name]`
that is distinguishable from a successful-but-empty result.

**Actual behavior:** the failure is stored as `result.data` (frequently
`{}`), and the orchestrator logs `tool_executed ... success=True` -- a false
positive -- with no error or warning log anywhere.

**Evidence:** `tests/unit/test_orchestrator.py::test_run_logs_and_preserves_failed_tool_result`
(commit `5f573fb`) constructs a fake tool that fails the same way every real
tool fails (returns `ToolResult(success=False, ...)` without raising), runs
it through the actual `Orchestrator.run()`, and shows: no error/warning log
is emitted, `output["tool_results"]["tech_detector"] == {}`, and the captured
log explicitly contains `('info', 'tool_executed', {'tool': 'tech_detector',
'success': True})`.

### Map

- **`agent/orchestrator.py` -- `Orchestrator.run()` (lines 51-62):** primary
  fix location. Must branch on `result.success` before deciding what to log
  and what to store in `results[tool_name]`.
- **`agent/orchestrator.py` -- `Orchestrator._execute_tool()` (lines 136-173):**
  currently catches `TimeoutError`/`Exception` and re-raises after logging --
  this part already works correctly for genuinely raised exceptions and
  should be left alone, but its interaction with the new `result.success`
  check in `run()` needs to stay consistent (one failure shape regardless of
  whether the tool raised or returned `success=False`).
- **`agent/tools/base.py` -- `ToolResult` dataclass (`success: bool, data:
  dict, error: str | None`):** defines the contract the orchestrator must
  start honoring. Not expected to change.
- **`agent/tools/github_tool.py`, `tech_detector.py`, `readme_scorer.py`,
  `skill_extractor.py`, `market_analyzer.py`:** read-only reference -- each
  confirms the `ToolResult(success=False, error=...)` contract on failure.
  Not expected to change.
- **`agent/error_handling.py` -- `retry_with_backoff`, `RetryContext`:**
  listed as relevant in the issue, but investigation shows it already
  re-raises `last_exception` correctly and logs at warning/error level on
  each retry attempt. It is not the source of the silent-swallowing bug for
  any of the current tools, since none of them let exceptions reach it in
  the failure case. Kept in scope for Week 9 only to confirm no related edge
  case (e.g. `max_retries=0` never entering the loop and returning `None`
  silently) needs a fix alongside the main change.
- **`agent/memory/context_manager.py` -- `store_tool_result` /
  `get_tool_result`:** currently caches whatever `_execute_tool` returns,
  including a failed `ToolResult`, unconditionally. Relevant because a fix
  that changes what gets returned/cached from `_execute_tool` also changes
  what gets memoized as a "cache hit" on a later call.
- **`tests/unit/test_orchestrator.py`:** existing reproduction test (added
  this week); expected to grow additional cases during the actual fix.

**Files expected to be modified during implementation (Week 9):**
- `agent/orchestrator.py`
- `tests/unit/test_orchestrator.py`
- Possibly `agent/error_handling.py`, only if the `max_retries=0` edge case
  (see Risks) is judged in-scope.

### Plan

1. In `Orchestrator.run()`, replace the unconditional
   `results[tool_name] = result.data` / `logger.info(..., success=True)` with
   a branch on `result.success`: on failure, call
   `logger.error("tool_execution_failed", tool=tool_name, error=result.error)`
   and store a failure-shaped value in `results[tool_name]` (e.g.
   `{"success": False, "error": result.error}`), matching the shape already
   used by the existing `except Exception` branch at lines 60-62 so callers
   see one consistent failure format regardless of path.
2. Only log `logger.info("tool_executed", tool=tool_name, success=True)` in
   the branch where `result.success` is actually `True`.
3. Decide (and document the decision inline) whether *successful* results
   should also be wrapped in a consistent envelope (e.g.
   `{"success": True, "data": ...}`) or left as bare `result.data` for
   backward compatibility -- this is a real design fork with downstream
   consequences (see Risks) and should be resolved before writing the fix,
   not discovered while writing it.
4. Extend `tests/unit/test_orchestrator.py` to cover: a tool that raises
   directly (confirm the pre-existing exception path still logs/returns
   consistently with the new `ToolResult`-based path), the existing
   "unknown tool" `ValueError` path (no regression), and a genuine success
   case (no regression in the happy path).
5. Re-run the full unit suite (`.venv/bin/pytest tests/unit -v -m unit`) and
   confirm the failure count only decreases by the tests this issue touches
   -- there are 53 pre-existing unrelated failures in this repo that are out
   of scope and must not be conflated with this fix.

### Inputs & outputs

**Inputs:**
- `profile_id: str` and `profile_data: dict` passed into `Orchestrator.run()`.
- The `(tool_name, tool_input)` pairs produced by `_build_plan()` (unchanged
  by this fix).
- The `ToolResult(success, data, error)` object returned by each tool's
  `execute()`.

**Outputs:**
- The dict returned by `run()`: `{"profile_id", "tool_results",
  "cached_results"}`. After the fix, `tool_results[tool_name]` must have a
  shape that lets a caller distinguish "tool succeeded with this data" from
  "tool failed with this error" for every tool, not just the ones that
  happened to raise an unregistered-tool `ValueError`.
- Structlog output: exactly one error-level log entry per failed tool call,
  and no misleading `success=True` info log for a tool that failed.

### Risks & unknowns

- **Breaking change to `tool_results` shape:** wrapping failure results
  (and possibly success results, per Plan step 3) changes what downstream
  code receives from `results[tool_name]`. Today nothing in the app actually
  consumes this shape in production -- `core/services/review_service.py`'s
  `_run_agent_orchestration()` is a hardcoded placeholder and does not call
  `Orchestrator` at all (confirmed by reading the file and grepping for
  `Orchestrator` usage repo-wide: it's only referenced inside
  `agent/orchestrator.py` itself). This lowers the immediate blast radius,
  but should be verified again in Week 9 in case that wiring changes before
  this fix lands.
- **Caching of failed results:** `_execute_tool` caches whatever it gets
  back from `_execute_with_timeout` via `context_manager.store_tool_result`,
  including a failed `ToolResult`, unconditionally. Need to verify whether a
  failed result should be cached at all -- as written today, a failure is
  memoized and would be replayed as a "cache hit" on a later call within the
  same session, silently skipping any retry.
- **`retry_with_backoff(max_retries=0)`:** if `max_retries` were ever `0`,
  the `while attempt < max_retries` loop never executes, `last_exception`
  stays `None`, and the wrapper falls through returning `None` with nothing
  raised -- a separate latent bug in `agent/error_handling.py`. Current
  orchestrator usage always passes `max_retries=2`, so this is not reachable
  today, but should be double-checked before Week 9 sign-off.
- **Timeout is measured, not enforced:** `_execute_with_timeout` computes
  `elapsed` and only logs a `tool_slow` warning if it exceeds `timeout` --
  there is no actual timeout mechanism (no thread/async cancellation), so a
  hanging tool call blocks indefinitely regardless of `tool_timeout`. Related
  to this issue's theme (failures not surfaced) but a distinct bug; flagging
  it here so it isn't silently folded into this fix without a deliberate
  decision.
- **Zero pre-existing test coverage:** there was no test file for
  `agent/orchestrator.py` or `agent/error_handling.py` before this week, so
  the fix's regression risk is higher than for a well-tested module --
  mitigated by Plan step 4's expanded test cases.
- **mypy/pre-commit tooling is currently broken in this dev environment,**
  independent of this issue: this Python 3.14 venv's `mypy` (pinned to
  `v1.8.0` in `.pre-commit-config.yaml`) fails on a numpy type-stub syntax
  error before it can check anything, and `agent/orchestrator.py`,
  `error_handling.py`, `context_manager.py`, and `session_store.py` already
  fail `disallow_untyped_defs=true` independent of any change here (verified
  by running `mypy agent/orchestrator.py --ignore-missing-imports` in
  isolation). Unknown whether CI runs a different Python version where this
  resolves itself -- needs checking (e.g. `.github/workflows/`) before the
  Week 9 PR, since the final fix will need to pass mypy cleanly on whatever
  functions it touches at minimum.

### Edge cases

- A tool returns `ToolResult(success=False, data={}, error=None)` (failed,
  but with no error message) -- the fix must not crash while trying to log a
  `None` error message.
- A tool raises an exception directly instead of returning
  `ToolResult(success=False, ...)` (e.g. a bug in a future tool that doesn't
  follow the existing convention) -- the pre-existing `except Exception`
  path in `run()` must produce the same failure shape as the new
  `result.success is False` path, not two different formats.
- The existing "unknown tool" case (`tool_name not in self.tools`, raises
  `ValueError`) must continue to log and return exactly as it does today --
  this already works correctly and is a regression risk if touched carelessly.
- Two or more tools fail within the same `run()` call -- `results` must
  reflect each tool's own outcome independently, not just the last one
  processed in the loop.
- A tool fails on its first attempt but succeeds after a retry inside
  `retry_with_backoff` -- the final logged outcome must reflect the
  eventual success, not the earlier retry warning.
