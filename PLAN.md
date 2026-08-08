## Solution plan

**Issue:** [Issue #43 — Agent session state is not cleared between reviews for the same user](https://github.com/ascherj/pathreview/issues/43)

### Understand

The normal review-processing flow does not currently invoke the real agent orchestrator. `create_review_endpoint()` in `api/routes/reviews.py` schedules `process_review()` in `core/services/review_service.py`, but `_run_agent_orchestration()` currently returns a hardcoded dictionary. This feature gap prevents the session-state issue from being reproduced through reviews created in the browser or API.

The underlying state-isolation problem exists in `agent/orchestrator.py`. `Orchestrator.__init__()` creates one `ContextManager`, and that same context manager remains attached to the orchestrator across repeated calls to `run()`. `ContextManager` memoizes tool results using the tool name and a hash of the tool input. Because the context is not cleared at the beginning of a new review, a later run with the same tool input can receive a cached result from an earlier run rather than executing the tool again.

`Orchestrator.run()` accepts `profile_id` and `profile_data`, but it does not accept a `review_id`. When a `SessionStore` is configured, the orchestrator reads and writes Redis state using only `profile_id`. Therefore, two separate reviews for the same profile are not identified by separate review-specific session keys.

The expected behavior is that every new review starts with clean review-specific agent state. Tools should run using the current review's input, and cached results or session data from an earlier review should not be reused.

The actual behavior is that a reused orchestrator retains its in-memory context cache, while persisted session state is associated only with the profile rather than the individual review.

### Map

The request and processing flow involves:

* `api/routes/reviews.py`

  * `create_review_endpoint()`
  * Creates the review and schedules `process_review()` through `background_tasks.add_task(...)`.

* `core/services/review_service.py`

  * `process_review()`
  * `_run_agent_orchestration()`
  * The current placeholder implementation prevents the normal application flow from reaching the real orchestrator.

The state-isolation issue involves:

* `agent/orchestrator.py`

  * `Orchestrator.__init__()`
  * `Orchestrator.run()`
  * `Orchestrator._execute_tool()`
  * Creates and reuses the context manager, checks cached tool results, and reads and writes stored state using `profile_id`.

* `agent/memory/context_manager.py`

  * `ContextManager.__init__()`
  * `ContextManager.store_tool_result()`
  * `ContextManager.get_tool_result()`
  * Stores memoized tool results in the in-memory `results` dictionary.
  * This file may need a clear or reset method.

* `agent/memory/session_store.py`

  * `SessionStore.get()`
  * `SessionStore.set()`
  * `SessionStore.delete()`
  * Already supports deletion, but the orchestrator currently uses `profile_id` as the session identifier.

Production tools that may be useful for the regression test include:

* `agent/tools/readme_scorer.py`
* `agent/tools/skill_extractor.py`
* `agent/tools/tech_detector.py`

Existing tests that can guide tool setup include:

* `tests/unit/test_readme_scorer.py`
* `tests/unit/test_skill_extractor.py`
* `tests/unit/test_tech_detector.py`

A new orchestrator regression test will likely be added at:

* `tests/unit/test_orchestrator.py`

The files most likely to change are:

* `agent/orchestrator.py`
* `agent/memory/context_manager.py`
* `tests/unit/test_orchestrator.py`

`agent/memory/session_store.py` may also change if review-specific Redis keys are required.

`core/services/review_service.py` is part of the discovered feature gap, but replacing its placeholder orchestration implementation may be outside the focused scope of Issue #43.

### Plan

1. Write a focused regression test before changing production code. Create one `Orchestrator` instance, invoke `run()` twice to represent two reviews for the same profile, and spy on an existing deterministic tool such as `ReadmeScorer` or `TechDetector`.

2. Use identical tool input in both runs and assert that the selected tool's `execute()` method is called twice. The current implementation is expected to fail this assertion because the second run can return the result cached by the persistent `ContextManager`.

3. Add an explicit review-boundary reset for the in-memory context. Either recreate `ContextManager` or add and call a clear method at the beginning of each new review, while preserving memoization between tools during a single review.

4. Determine the intended Redis session behavior. Either delete the previous profile session when a new review begins or change orchestration to use a review-specific session identifier. Confirm this by tracing all `SessionStore` callers before changing its key strategy.

5. Run the focused orchestrator regression test and the repository's full unit-test suite. Confirm that a second review executes its tools again and does not return cached results or stored state from the earlier review.

### Inputs & outputs

The fix currently receives:

* `profile_id`
* `profile_data`
* The execution plan created from `profile_data`
* Existing in-memory results held by `ContextManager`
* Existing Redis state returned by `SessionStore`, when configured

The current orchestration interface does not receive a `review_id`.

Before the fix:

* One orchestrator instance can reuse cached tool results across multiple calls to `run()`.
* Two reviews with the same tool input can resolve to the same context-manager cache key.
* Redis state for multiple reviews of the same profile uses the same profile-based session identifier.

After the fix:

* Every newly started review receives clean review-specific context.
* Tools execute again for a new review, even when the same profile and tool input are used.
* Cached results can still be reused within one review when appropriate.
* Results created during one review do not appear in a later review.
* Redis state is either cleared at the review boundary or identified using a review-specific key.

### Risks & unknowns

* `ContextManager` is intended for within-session memoization. Clearing it before every individual tool would break useful caching, so the reset must occur only at the new-review boundary.

* `Orchestrator.run()` has no `review_id`. It is still uncertain whether the intended architecture is to add `review_id`, reset state on every `run()` call, or instantiate a new orchestrator for every review.

* The loaded Redis `session_state` is currently updated and stored, but it is not directly passed into tool execution. More investigation is needed to determine whether Redis causes stale tool outputs or represents a separate persistence problem.

* `SessionStore.delete()` already exists. Calling it with `profile_id` may remove information that maintainers intended to preserve between reviews.

* `_run_agent_orchestration()` in `core/services/review_service.py` is still a placeholder. Connecting the real orchestrator could expand the issue into a larger integration task and may need to remain outside Issue #43.

* Some existing tools may depend on external services, LLM providers, or configuration. The regression test should use a deterministic production tool and spy on its execution without making network calls.

* Two reviews for the same profile may run concurrently. Clearing state using only `profile_id` could cause one review to delete or overwrite another review's active state.

### Edge cases

* The same profile starts two reviews with identical README, resume, or file input.
* The same profile starts a second review with changed input.
* Two different profiles are processed by the same orchestrator instance.
* A previous review completed and left cached tool results.
* A previous review failed after storing partial context or session state.
* No previous context or Redis session exists.
* The Redis session expired before the next review.
* Redis contains malformed data or is unavailable.
* A tool returns an empty result.
* A tool raises an exception.
* Two reviews for the same profile run concurrently.
* Context is cleared between reviews without being cleared between tools in the same review.
* Profile-level data that is intentionally reusable is not deleted with review-specific state.
