## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user [#43](https://github.com/jamjamgobambam/pathreview/issues/43)

### Understand
Root cause: The orchestrator loads a persisted session_state from the Redis-backed SessionStore at the start of run(), but it does not use that loaded state to populate the in-memory ContextManager or skip tool execution. Each Orchestrator instance creates a fresh ContextManager, so persisted results are not consulted/used to prevent re-running tools. Expected behavior: when a previous session result exists for the same profile and inputs, the orchestrator should reuse it instead of re-running slow/external tools. Actual behavior: session_state is loaded but ignored, leading to either re-execution or inconsistent use of stale data.

### Map
Files likely to touch:
- agent/orchestrator.py (primary): change run() to consult session_state and/or pre-populate ContextManager
- agent/memory/context_manager.py: ensure it can accept pre-loaded results (API already supports store_tool_result())
- agent/memory/session_store.py: read/write format validation (JSON) — ensure stored shape matches expectations
- tests/unit/test_orchestrator_session_store_cache.py: add reproduction test (already added)

### Plan
1. Add a failing unit test that demonstrates the cross-process/session behavior (done — tests/unit/test_orchestrator_session_store_cache.py).
2. Modify Orchestrator.run(): after loading session_state, iterate session_state items and pre-populate ContextManager results (by storing them with the same keys the ContextManager expects). Alternatively, check session_state before executing each tool and skip execution when a cached result exists.
3. Update ContextManager storage format if necessary — session_state keys must map to the same key convention ("{tool_name}:{input_hash}"). If session_state currently stores tool results under tool names only, adapt orchestrator to convert/derive keys (e.g., re-hash inputs or persist keys explicitly).
4. Add unit tests verifying:
   - New Orchestrator instance reuses session results and does not re-execute tools
   - When profile_data changes (inputs change), orchestrator re-executes tools and updates session store
5. Run test suite, iterate on any type or formatting issues, and commit changes.

### Inputs & outputs
Input: profile_id (string), profile_data (dict), SessionStore contents (JSON mapping of tool results)
Output: Orchestrator.run() should return tool_results sourced from SessionStore when appropriate and avoid re-executing tools unnecessarily. SessionStore should be updated with the merged fresh results.

### Risks & unknowns
- How session_state is structured in Redis today (what keys/nesting) — tests assume a mapping of tool_name -> result. If existing persisted shape differs, conversion will be needed.
- Race conditions: two concurrent requests for same profile may both try to run tools and update session store. Consider adding optimistic locking or last-write-wins approach.
- Detecting staleness: when profile_data changes, we must detect that stored results no longer apply. Approach: include input hashes when persisting or persist per-tool input hash keys.

### Edge cases
- Partial results: session_state might contain results for some tools but not others. Orchestrator should reuse available results and run only missing tools.
- Different input variations: ensure per-tool input hashing is used so results are only reused for matching inputs.
- Corrupted session data: handle JSON parse errors gracefully (session_store.get already handles decode errors).
