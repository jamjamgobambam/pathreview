## Solution plan

**Issue:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost (https://github.com/ascherj/pathreview/issues/47)

### Understand
Currently, the `Orchestrator` execution state is only persisted to the `SessionStore` (Redis) at the very end of the execution run. If the FastAPI server restarts or crashes during a long-running review, all intermediate tool results are lost because they were only held in-memory. The expected behavior is that the agent incrementally persists its state so that an interrupted session can resume where it left off, picking up previously processed results from the cache/DB.

### Map
The following files and components are involved:
- `agent/orchestrator.py` (specifically `Orchestrator.run` method where tool execution loops).
- `tests/unit/test_orchestrator_reproduction.py` (to ensure the new tests pass).

### Plan
1. **Locate Tool Execution Loop**: Open `agent/orchestrator.py` and locate the `for tool_name, tool_input in plan:` loop within the `run` method.
2. **Move Persistence Logic**: Inside this loop, immediately after a tool finishes execution (`_execute_tool`), update the `session_state` dict with the result and call `self.session_store.set(profile_id, session_state)`.
3. **Handle Exceptions Incrementally**: Ensure that if an exception is caught during tool execution, that failure state is also explicitly persisted before continuing to the next tool or exiting.
4. **Refactor for DRY**: Optionally extract the state update and `set` calls into a small helper method `_persist_state` to avoid duplicating the code in both the `try` and `except` blocks.

### Inputs & outputs
- **Inputs**: The `Orchestrator.run` method takes a `profile_id` (string) and `profile_data` (dict). Individual tools output their execution results as dictionaries.
- **Outputs**: The change does not alter the final returned dictionary of `run()`, but it changes the side effects—specifically, it produces repeated, incremental calls to `session_store.set(profile_id, session_state)`.

### Risks & unknowns
- **Performance Overhead**: Calling `session_store.set` requires a JSON serialization and a Redis network call. Doing this after every tool execution adds some overhead. Given Redis is fast and tasks are long-running, this is an acceptable tradeoff for resilience.
- **Race Conditions**: If there are concurrent background tasks attempting to update the same session store for the same `profile_id`, they could overwrite each other. Assuming reviews for a single profile run sequentially, this shouldn't be an issue.

### Edge cases
- Tools that crash unexpectedly (`KeyboardInterrupt` or process exit) might not reach the next iteration, but any previously completed tools will safely be stored in Redis.
- If Redis is down, `self.session_store.set` gracefully catches exceptions based on the `SessionStore` implementation, meaning it shouldn't crash the orchestrator, though persistence won't occur.
