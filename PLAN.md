## Solution plan

**Issue:** [Orchestrator catches all exceptions from tool calls and continues without logging the failure](https://github.com/ascherj/pathreview/issues/44)

### Understand
**Root cause:** The code hides the exact file and line number (stack trace) when a tool crashes, and only logs a simple error message.

**Expected vs. actual:** We expect the terminal to show the full stack trace so we can debug easily. Currently, it hides it.

### Map
Files to change:
- `agent/orchestrator.py`: Update error logs in `run` and `_execute_tool`.
- `agent/error_handling.py`: Update error logs in the retry functions.

### Plan
1. Find the `logger.error` calls in both files.
2. Add `exc_info=True` to them so they print the stack trace.
3. Run the app to verify the stack trace shows up in the terminal when a tool crashes.

### Inputs & outputs
**Input:** A tool crashes with an error.
**Output:** The terminal prints the full stack trace, making it easy to debug.

### Risks & unknowns
- **Messy logs:** Printing a stack trace for expected errors (like a 404) might make the logs too noisy.

### Edge cases
- **Timeouts:** Tool timeouts should still be handled cleanly without crashing the app.