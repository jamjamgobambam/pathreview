## Solution plan

**Issue:** [#44 - Orchestrator catches all exceptions from tool calls and continues without logging the failure](https://github.com/ascherj/pathreview/issues/44)

### Understand

The orchestrator assumes that any value returned by a tool represents success.
Several tools catch their own exceptions and return
`ToolResult(success=False, data={}, error=...)`, so the retry decorator never sees
an exception to retry. `Orchestrator.run()` then stores only `result.data`, discards
the `success` and `error` fields, and logs `tool_executed` with `success=True`.

When a tool does raise an exception, `retry_with_backoff` correctly catches it
because the default `(Exception,)` tuple includes normal application exceptions.
After retries are exhausted, the decorator re-raises the exception, but `run()`
catches it, converts it to an error dictionary, and continues executing the plan.

Expected behavior is for the orchestrator to recognize both forms of tool failure,
record accurate failure information, and surface a clear error rather than treating
the tool call as successful or silently returning incomplete results.

### Map

- `agent/orchestrator.py`
  - `Orchestrator.run()`: interprets tool results, logs their status, and currently
    suppresses raised exceptions.
  - `Orchestrator._execute_tool()`: executes and caches tool results.
  - `Orchestrator._execute_with_timeout()`: applies `retry_with_backoff`.
- `agent/error_handling.py`
  - `retry_with_backoff()`: retries raised exceptions and re-raises the final one.
    No change is currently expected here because `(Exception,)` already catches
    the relevant raised exceptions.
- `agent/tools/base.py`
  - `ToolResult`: defines the `success`, `data`, and `error` fields the orchestrator
    must preserve and inspect.
- `tests/unit/test_orchestrator.py`
  - Contains controlled test doubles and regression tests for returned failures
    and raised exceptions.

### Plan

1. Update `Orchestrator.run()` to distinguish a successful `ToolResult` from a
   failed one instead of checking only whether the object has a `data` attribute.
2. Preserve a failed result's `success` and `error` information in the returned
   `tool_results` structure, and emit a failure log rather than
   `tool_executed(..., success=True)`.
3. Decide at the orchestration boundary whether an exhausted raised exception
   should stop the full run or be represented as a clearly surfaced per-tool
   failure; apply that behavior consistently without hiding the exception.
4. Prevent failed `ToolResult` objects from being cached as successful tool output,
   so later calls cannot reuse an empty or failed result as a cache hit.
5. Extend and run the orchestrator unit tests to cover successful results, returned
   failures, retry exhaustion, logging, cache behavior, and whether later plan
   entries execute under the chosen failure policy.

### Inputs & outputs

The fix takes the existing execution plan entries, tool inputs, returned
`ToolResult` objects, and exceptions raised by `tool.execute()`.

For successful tools, behavior remains unchanged: return the tool's data, log a
successful execution, and cache the result. For failed tools, retain a structured
failure containing at least `success=False` and the error message, log it as a
failure, do not cache it as usable output, and surface the failure according to the
selected orchestration policy.

### Risks & unknowns

- The issue wording says to "surface a clear error," but it must be confirmed
  whether one tool failure should abort the entire plan or allow remaining tools to
  run while returning an explicit partial-failure response.
- Changing the shape of `tool_results` for failures may affect API or frontend code
  that currently expects each value to contain only tool data.
- Some tools intentionally use `ToolResult(success=False)` for expected conditions,
  such as missing input or an unavailable repository. These may need to remain
  recoverable rather than aborting the whole review.
- Existing cached failed results may remain until their cache entries expire or are
  cleared.

### Edge cases

- A tool returns `ToolResult(success=False)` with an error message.
- A tool returns `ToolResult(success=False)` without an error message.
- A tool raises a retryable exception on every attempt.
- A tool fails initially and then succeeds on a retry.
- A tool returns a successful result with empty data.
- An unknown tool name is included in the plan.
- A failed tool is followed by additional tools in the plan.
- A cached result is itself unsuccessful or malformed.
