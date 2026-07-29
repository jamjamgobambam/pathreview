## Solution plan

**Issue:** Agent session state leaks between consecutive reviews for the same profile.

### Understand
The issue appears in the orchestrator flow. Each run loads any existing session payload for the profile ID from the session store, merges new tool results into it, and writes the combined state back. Because the same profile ID is reused across reviews, stale context from an earlier review can persist into the next one. The expected behavior is that a new review should begin with a fresh session state unless the workflow explicitly intends to resume or continue an existing session.

### Map
Likely files involved:
- agent/orchestrator.py: loads and persists session state for each run
- agent/memory/session_store.py: serializes and retrieves session data from storage
- agent/memory/context_manager.py: may need adjustment if cached tool results also contribute to stale context

### Plan
1. Inspect the orchestrator flow to confirm exactly when session state is loaded, merged, and saved for a profile.
2. Change the session-handling logic so a new review starts from a clean state unless a resume path is explicitly requested.
3. Ensure the session store is cleared or overwritten in a way that prevents stale review data from surviving into later runs.
4. Add a regression test that performs two consecutive reviews for the same profile and verifies the second run does not inherit stale session data from the first.
5. Run the relevant unit tests and verify the behavior in the local environment.

### Inputs & outputs
The fix will take the profile ID and the current review input as inputs. It should produce a fresh session payload for the new review and prevent previous review state from being reused unless explicit resume behavior is intended.

### Risks & unknowns
The main risk is that some parts of the workflow may intentionally rely on cached or persisted state across runs. I will confirm whether that behavior is desired before changing the persistence logic. A second risk is that clearing state too aggressively could remove useful context in cases where partial reuse is actually expected.

### Edge cases
The fix should handle:
- two consecutive reviews for the same user with different inputs
- a review after a failed or partial previous run that left behind partial session data
- a review where no prior session data exists
- a review where the same profile ID is reused after a different input set and should not inherit stale results
