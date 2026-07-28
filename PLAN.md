## Solution plan

**Issue:** [Agent session state is not cleared between reviews for the same user](https://github.com/ascherj/pathreview/issues/47)

### Understand

The expected behavior is that every review gets isolated agent state, even when two reviews belong to the same profile. The actual behavior is that `Orchestrator.run()` receives a `profile_id` and passes it to `SessionStore.get()` and `SessionStore.set()`. `SessionStore` then stores both reviews under the same `session:{profile_id}` Redis key, so a later review overwrites the earlier review's persisted state. The local reproduction in `tests/unit/test_session_state_reproduction.py` confirms that the first review cannot be retrieved after the second review is stored.

### Map

Likely files to touch:

- `core/services/review_service.py` — pass the current `review_id` into the agent orchestration boundary.
- `agent/orchestrator.py` — accept a review/session identifier and use it for session load/save operations.
- `agent/memory/session_store.py` — keep the session-key contract explicit and add or clarify deletion/expiration behavior if needed.
- `tests/unit/test_session_state_reproduction.py` — convert the reproduction into a regression test using two distinct review IDs.
- A new or existing orchestrator unit-test module under `tests/unit/` — verify that load/save calls use the review ID and that separate runs do not share state.

### Plan

1. Trace the real `process_review()` to agent call path and decide whether `review_id` should be a required orchestrator argument or a separately named `session_id`, documenting the chosen contract in the affected docstrings.
2. Update `core/services/review_service.py` and `agent/orchestrator.py` so each review loads and persists state with its own review/session identifier rather than `profile_id`.
3. Add regression coverage for two reviews on one profile, including assertions that Redis receives two distinct keys and that each review retrieves only its own state.
4. Add cleanup/TTL assertions where appropriate, then run the targeted unit tests and the project lint/type checks; investigate any failures that are unrelated to this issue separately.

### Inputs & outputs

The fix takes the existing profile data plus the current `review_id` at the orchestration boundary. It should produce the same tool-result structure and review output as today, while reading/writing `session:{review_id}` (or an equivalent explicitly documented session key) so each review has isolated persisted state. The profile remains an input for analysis, but it is no longer the persistence namespace.

### Risks & unknowns

- `core/services/review_service.py` currently contains a placeholder `_run_agent_orchestration()` implementation, so the final production call signature may need to be aligned with the eventual real orchestrator wiring rather than changed in isolation.
- `agent/orchestrator.py` currently has no `review_id` parameter and its in-memory `ContextManager` is instance-scoped; tests must distinguish Redis persistence isolation from same-instance memoization.
- Existing callers or hidden tests may call `Orchestrator.run(profile_id, profile_data)` positionally. The compatibility strategy for adding the identifier must be checked before changing the signature.
- The repository currently reports a pre-existing mypy error at `agent/memory/session_store.py:41`; the fix should avoid masking it and should verify whether the touched files can be checked independently.

### Edge cases

- Two reviews for the same profile run sequentially: the second review must not retrieve or overwrite the first review's session.
- Two reviews for the same profile run concurrently: each must use its own identifier, even when their tool plans or profile inputs are identical.
- A review has no existing Redis state or its state has expired: orchestration should start with an empty state and still persist under that review's key.
- A session identifier is a UUID object at the service boundary rather than a string: key construction and logging must remain stable and consistent.
