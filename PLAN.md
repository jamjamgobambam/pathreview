# Solution Plan

**Issue:** Issue #47 - Agent state isn't persisted across API restarts
(Link: <PASTE_GITHUB_ISSUE_LINK>)

## Understand

The orchestrator loads existing session state from Redis before executing tools, but it only saves the updated session after all tools finish executing.

If the API restarts during execution, completed tool results remain only in memory and are lost before they are written to Redis. The workflow cannot resume from where it stopped.

Expected behavior:
- Completed tool results should be checkpointed and survive an API restart.
- The orchestrator should resume instead of restarting the entire workflow.

Actual behavior:
- Session state is written only after all tools complete.
- Intermediate progress may be lost if the process stops before the final save.

## Map

Files involved:

- `agent/orchestrator.py`
  - `Orchestrator.run()`
- `agent/memory/session_store.py`
- `agent/memory/context_manager.py`
- Orchestrator tests (existing or new)

## Plan

1. Add a test that simulates an interrupted workflow.
2. Save session state after each successful tool execution.
3. Skip tools whose results already exist in Redis.
4. Verify the workflow resumes correctly after restart.

## Inputs & Outputs

Inputs:
- profile_id
- profile_data
- existing Redis session

Outputs:
- checkpointed session after each completed tool
- resumed workflow after restart
- final review containing all completed tool results

## Risks & Unknowns

- Additional Redis writes may affect performance.
- Some tool results may not be JSON serializable.
- Need to determine how failed tools should behave after restart.

## Edge Cases

- Redis unavailable
- Missing session
- Corrupted session
- Partial execution
- Multiple reviews for the same profile