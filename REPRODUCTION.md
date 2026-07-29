# Reproduction Notes: Session state persistence across reviews

## Issue
Agent session state is not cleared between reviews for the same user.

## Reproduction steps
1. Create a session store entry for a known profile ID with stale data from an earlier review.
2. Invoke the orchestrator for the same profile ID again with a new review payload.
3. Observe that the orchestrator loads the old session state from the session store before running the new plan.

## Expected behavior
A new review should start with a fresh session state unless the workflow explicitly intends to preserve prior data.

## Observed behavior
The orchestrator currently does the following in agent/orchestrator.py:
- loads prior state with `self.session_store.get(profile_id) or {}`
- merges new results into that state with `session_state.update(results)`
- writes the merged state back to the session store

This means stale values from an earlier review can persist into a later review for the same profile ID.
