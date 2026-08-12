## Solution plan

**Issue:** Orchestrator catches all exceptions from tool calls and continues without logging the failure ([#44](https://github.com/ascherj/pathreview/issues/44))

### Understand

**Expected behavior:** When a tool fails (raises after retries are exhausted, or times out), the failure must be impossible for calling code to miss. Either the exception propagates out of `Orchestrator.run()`, or the returned dict carries an unambiguous, top-level signal ("this run had a failure") in addition to the per-tool detail.

**Actual behavior:** `Orchestrator.run()` (`agent/orchestrator.py:53-62`) wraps each tool call in `try / except Exception`. On failure it logs `tool_execution_failed` and writes `results[tool_name] = {"error": str(e), "success": False}` — a dict with the exact same shape (`dict[str, Any]`) as what a successful `BaseTool` might already return via `ToolResult.data` (see `agent/tools/github_tool.py:37-40`, which itself returns a `success: False` payload instead of raising for missing input). Because both "tool raised" and "tool returned data containing a `success` key" collapse into the same `results[tool_name]` slot, and because `run()`'s top-level return dict (`orchestrator.py:72-76`) has no `success` / `errors` field of its own, nothing forces a caller to distinguish "everything worked" from "one or more tools silently blew up." The reproduction test (`tests/unit/test_orchestrator.py`) confirms this: a tool that always raises still produces a normal-looking `run()` result with no top-level failure indicator.

**Root cause:** the plan-execute loop treats "tool raised an exception" and "tool result payload" as the same kind of thing and merges them into one dict with no distinguishing metadata at the level `run()` returns to its caller. `_execute_tool` (`orchestrator.py:136-173`) and `_execute_with_timeout` (`orchestrator.py:175-202`) already do the "right" thing internally — they let `TimeoutError` and other exceptions propagate up to `run()` — the bug is entirely in how `run()`'s loop absorbs what they let through.

### Map

Files to touch:
- `agent/orchestrator.py` — `Orchestrator.run()` (the loop at lines 53-62 and the return dict at 72-76) is the primary fix site: track failures separately from `tool_results`, and add a top-level indicator (e.g. `"success": bool` and/or `"failed_tools": {...}`) to the dict `run()` returns.
- `agent/error_handling.py` — no behavioral change expected, but double-check `retry_with_backoff` and `RetryContext` don't themselves swallow anything once `run()`'s contract changes (they currently re-raise correctly after exhausting retries, so they're probably fine as-is; will confirm with tests rather than assume).
- `tests/unit/test_orchestrator.py` — extend past the single reproduction test: cover partial-failure (some tools succeed, one fails), all-failure, and confirm session persistence still stores whatever the new failure representation is.

Out of scope (confirmed in Week 7 issue selection): wiring `Orchestrator` into `review_service.py` / the live API. It isn't called from the review pipeline today, so the fix stays contained to the module and its tests.

### Plan

1. Decide and document the failure contract: `run()` will keep `tool_results` as today (one entry per tool, success or failure), but add a top-level `"success": bool` key (False if any tool failed) and a `"failed_tools": list[str]` key naming which tools failed, so callers get an O(1) check instead of having to scan every entry in `tool_results` for a `success` key that might not even be there (a plain `ToolResult.data` dict may not have a `success` key at all).
2. Update the loop in `run()` to track failures in a local `failed` list alongside populating `results`, then use it to build the new top-level keys before returning.
3. Decide whether a fully-failed run (every tool raised) should also raise from `run()` itself, vs. always returning normally with `success: False`. Leaning toward "always return normally with the flag" since `run()` is meant to aggregate multiple independent tool calls — a single bad tool shouldn't necessarily blow up the whole profile analysis — but will sanity-check this against how the issue is phrased ("must handle the failure explicitly") and any related tests/mentors feedback before finalizing.
4. Add regression tests: all-succeed (existing shape unaffected), one-fails-rest-succeed (`success: False`, `failed_tools: ["x"]`, other tools' results untouched), all-fail, and a session-persistence test confirming `session_store.set()` still gets called with the augmented results.
5. Update the reproduction test (`test_orchestrator_surfaces_tool_failure`) to assert against the finalized contract exactly, and add a docstring note pointing at the commit/PR that fixed it (or just leave it passing once the fix lands — either is fine, will decide based on what reads more clearly in the diff).

### Inputs & outputs

- **Input:** unchanged — `Orchestrator.run(profile_id: str, profile_data: dict)`.
- **Output:** `run()`'s return dict gains two keys: `"success": bool` (False if any tool in the plan failed) and `"failed_tools": list[str]` (empty if `success` is True). `tool_results` keeps its current per-tool shape so nothing downstream that already reads `tool_results[tool_name]` breaks.

### Risks & unknowns

- ~~Need to confirm no other code currently depends on `run()`'s return dict having *exactly* the three keys it has today~~ — resolved: `Orchestrator` isn't wired into the API/review pipeline, and a repo-wide grep found no other code reading `run()`'s return value, so adding keys is safe.
- ~~Whether "any tool fails" should also fail the *whole* `run()` call~~ — resolved: went with always returning normally plus a `success: False` / `failed_tools` flag, not raising. `run()` aggregates several independent tool calls; one bad tool shouldn't blow up the whole profile analysis, and this keeps the fix backward-compatible for any future caller that only reads `tool_results`.
- ~~`RetryContext` unused-code question~~ — resolved: confirmed via grep it's referenced nowhere outside `error_handling.py` itself. Left it in place (removing it is unrelated to this issue's scope) but flagged it as a separate cleanup task rather than silently ignoring it.

### Edge cases

- Every tool in the plan fails (empty successful results, `results` dict full of error entries).
- Empty plan (`profile_data` has none of `github_username`/`files`/`readme_content`/`resume_text` set) — `run()` should still return a well-formed dict with `success: True` and empty `tool_results`/`failed_tools`, not crash on an empty loop.
- A tool that raises `TimeoutError` specifically (already re-raised distinctly in `_execute_tool`) vs. a tool that raises a generic `Exception` — both must end up reflected the same way in the new top-level `failed_tools` list.
- A tool whose cached result (`context_manager.get_tool_result`) is reused instead of re-executed — a previously-successful cached result should never be misreported as a failure.
