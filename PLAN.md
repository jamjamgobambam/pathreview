## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user](https://github.com/jamjamgobambam/pathreview/issues/43)

### Understand

The agent orchestrator persists tool results into session state using the profile/session identifier, then merges new results into the previous state. The expected behavior is that a new review starts with clean tool state, while memoization can still be reused inside one review run. The actual behavior is that results from an older review can remain in the persisted session after a later review for the same profile no longer runs those tools.

### Map

Files I expect to touch:

- `agent/orchestrator.py`
- `agent/memory/session_store.py`
- `tests/unit/test_orchestrator_session_state.py`
- `docs/JOURNAL.md`

Related files to inspect before changing production code:

- `agent/memory/context_manager.py`
- `core/services/review_service.py`
- `api/routes/reviews.py`

### Plan

1. Add a focused failing unit test that reproduces two reviews for the same profile and proves stale tool results are not carried across the review boundary.
2. Decide the smallest review-boundary API change: either clear the stored session at the start of a new review or scope session keys by a review-specific identifier.
3. Update the orchestrator/session-store path so persisted state cannot merge old review results into a new review.
4. Keep in-memory `ContextManager` memoization available only within a single orchestrator run or explicitly scoped review session.
5. Run the relevant unit tests and update `docs/JOURNAL.md` with the final result in Week 9.

### Inputs & outputs

Input to the fix is a new review request for an existing profile/user, plus the profile data used to build the agent tool plan. The output should be freshly computed tool results for that review, with persisted session state containing only results that belong to the current review boundary.

### Risks & unknowns

The main risk is clearing too much state and removing useful within-review memoization. Another unknown is that `core/services/review_service.py` currently has placeholder orchestration logic, so I need to confirm where the real orchestrator will be wired before choosing the final public method signature.

### Edge cases

The fix should handle a second review that has fewer inputs than the first review, an empty tool plan, failed tool executions, repeated reviews for the same profile, and concurrent reviews that should not overwrite each other's session state.
