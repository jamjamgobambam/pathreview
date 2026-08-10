# Solution Plan — Issue #44

**Issue:** Orchestrator catches all exceptions from tool calls and continues without logging the failure #44. https://github.com/ascherj/pathreview/issues/44 

### Understand
* **Root Cause:** In `agent/orchestrator.py`, exceptions thrown during tool execution in `_execute_tool` and `_execute_with_timeout` are logged using `str(e)` instead of `exc_info=True`. Also, `run()` catches exceptions per tool and records `{"success": False}` without logging the full traceback or warning downstream tools.
* **Expected vs. Actual:** Expected behavior is for tool errors to log full exception/stack trace context (`exc_info=True`) and for intermediate retries in `error_handling.py` to log warnings. Actual behavior is silent swallowing of stack traces and retries.

### Map
* `agent/orchestrator.py`: Update `_execute_tool`, `_execute_with_timeout`, and `run()` to log full exception traces using `exc_info=True`.
* `agent/error_handling.py`: Add logging to `retry_with_backoff` to log intermediate attempt failures.
* `tests/unit/test_orchestrator.py`: Update tests to assert `exc_info` presence once fixed.

### Plan
1. Update `_execute_tool` / `run()` in `orchestrator.py` to include `exc_info=True` in error logs.
2. Update `@retry_with_backoff` in `error_handling.py` to log retry warnings on caught attempts.
3. Update unit tests to verify structured stack traces are captured when tools crash.

### Inputs & Outputs
* **Input:** Tool execution throwing an unhandled exception.
* **Output:** Structured error log with full stack trace (`exc_info`) while allowing orchestrator execution to handle tool failures gracefully.

### Risks & Unknowns
* Log verbosity in production if tools fail repeatedly (mitigated by rate of retry attempts).

### Edge Cases
* Timeouts (`TimeoutError`) vs unexpected code crashes (`AttributeError`, `KeyError`).