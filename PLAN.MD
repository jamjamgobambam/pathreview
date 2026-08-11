# Plan: Issue #44 - Add Top-Level Partial Failure Indicator in Orchestrator

## 1. Understand
- **Current Behavior:** When a tool fails during `orchestrator.run()`, `_execute_tool()` catches the exception and returns `{"error": ..., "success": False}` inside the nested results dictionary. The orchestrator continues processing and returns the final dictionary without indicating at the top level that the review is incomplete.
- **Expected Behavior:** `orchestrator.run()` should inspect tool outcomes and include a top-level boolean flag (`partial_failure: True`) in its returned dictionary whenever one or more tools fail.

## 2. Map
- `agent/orchestrator.py`: Modify the `run()` method to evaluate tool results and append the top-level flag.
- `agent/error_handling.py`: Verify existing error logging utilities.
- `tests/unit/test_orchestrator.py`: Unit tests verifying top-level flag behavior on tool failure and success.

## 3. Plan
1. In `agent/orchestrator.py`, locate the `run()` method where tool execution results are collected into the final return dictionary.
2. Iterate through the executed tool outputs in `tool_results`.
3. Set `partial_failure = True` on the top-level dictionary if any tool has `success == False`. Otherwise, set `partial_failure = False`.
4. Update `tests/unit/test_orchestrator.py` to assert that `partial_failure` is `True` when a tool fails and `False` when all tools succeed.

## 4. Inputs & Outputs
- **Input:** Profile ID (`str`) and profile data (`dict`) passed to `Orchestrator.run()`.
- **Output:** Response dictionary containing `tool_results` (`dict`) and `partial_failure` (`bool`).

## 5. Risks
- Potential schema mismatch if downstream handlers or APIs strictly validate response keys. Setting `partial_failure` consistently as a boolean (`False` on default success) mitigates unexpected `KeyError` exceptions.

## 6. Edge Cases
- All tools execute successfully -> `partial_failure` is `False`.
- No tools are executed -> `partial_failure` is `False`.
- Multiple tools fail -> `partial_failure` is `True`.