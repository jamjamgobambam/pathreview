## Solution plan

**Issue:** Agent session state is not cleared between reviews for the same user

### Understand
The bug appears to come from the orchestrator reusing persisted session data for the same profile ID across runs. In the current implementation, the orchestrator loads prior session state from the session store and merges it into the next run, which can cause stale context from a previous review to leak into a new review. The expected behavior is that a fresh review should begin with an empty or reset session state rather than inheriting previous review context.

### Map
Likely files involved:
- agent/orchestrator.py
- agent/memory/session_store.py
- potentially agent/memory/context_manager.py if the fix needs to clear or isolate cached tool results

### Plan
1. Inspect the orchestrator flow to confirm when session state is loaded and persisted for a profile.
2. Update the session-handling logic so a new review starts from a clean state unless the workflow explicitly intends to reuse state.
3. Add or adjust a regression test that reproduces two consecutive reviews for the same profile and verifies the second review does not inherit stale session data.
4. Run the relevant unit tests and review the behavior in the local environment.

### Inputs & outputs
The fix will take the profile ID and the current review input as input. It should produce a fresh session payload for the new review and ensure no stale state is reused unless explicitly requested.

### Risks & unknowns
The biggest risk is that some parts of the workflow may intentionally rely on cached state across runs. I need to verify whether that behavior is desired before changing the persistence logic. Another concrete risk is that clearing the state too aggressively could remove useful data in the same profile session if the product expects partial reuse. This uncertainty is tied to the logic in agent/orchestrator.py and the serialization behavior in agent/memory/session_store.py.

### Edge cases
The fix should handle:
- two consecutive reviews for the same user with different inputs
- a review after a failed or partial previous run that left behind partial session data
- a review where no prior session data exists
- a review where the same profile ID is reused after a different input set and should not inherit stale results
