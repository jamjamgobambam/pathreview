## Solution plan
 
**Issue:** Agent session state is not cleared between reviews for the same user
https://github.com/ascherj/pathreview/issues/43
 
### Understand
 
The `Orchestrator` class (`agent/orchestrator.py`) caches individual tool
results in a `ContextManager` instance (`self.context_manager`), keyed only
by a hash of the tool's input parameters (`_execute_tool`). This cache has
no expiration (TTL) and nothing ever clears it between review requests.
 
Expected behavior: when a user requests a second review of their profile
(for example, after updating their portfolio), each tool should be re-run
so the review reflects current, real data.
 
Actual behavior: if a tool's input parameters look the same across two
review requests (e.g. the same `github_repo` name, even though the repo's
contents may have changed since), `_execute_tool` finds a cache hit and
returns the old result without executing the tool again. The user's second
review can silently reuse data from their first review.
 
I confirmed this locally with a standalone script (see reproduction commit)
that shows a tool's `execute()` method is only called once even when the
orchestrator processes two separate "review" requests for the same profile.
 
### Map
 
Files I expect to touch:
- `agent/orchestrator.py` — contains `Orchestrator._execute_tool` (the
  caching logic itself) and `Orchestrator.run` (where session state is
  loaded/saved via `SessionStore`, currently without any explicit clearing
  step for a new review request).
- `agent/memory/context_manager.py` — the `ContextManager` class that
  performs the actual caching; likely needs either a TTL, a way to be reset,
  or to be scoped per-review instead of per-orchestrator-instance.
- `agent/memory/session_store.py` — not itself buggy, but I may need to add
  a `delete()` call somewhere in the review flow if session state should be
  explicitly cleared at the start of a new review.
- Possibly a test file, e.g. `tests/agent/test_orchestrator.py` (need to
  confirm exact test directory structure), to add a regression test based
  on my reproduction script.
### Plan
 
1. Confirm exactly how `ContextManager` stores and looks up cached results
   (read `agent/memory/context_manager.py` in full) to understand whether
   the cleanest fix is a TTL, an instance-per-request pattern, or an
   explicit cache-clearing call.
2. Decide on the fix approach: most likely, make `ContextManager`'s cache
   scoped to a single `run()` call (e.g. create a fresh `ContextManager` at
   the start of `run()`, or accept one as a constructor/parameter) rather
   than living for the whole lifetime of the `Orchestrator` instance.
3. Update `Orchestrator.run()` and/or `_execute_tool()` so that a new review
   request cannot see cached tool results from a previous, separate review.
4. Add/expand the `SessionStore` interaction if needed, so that stored
   session state is explicitly cleared or replaced (not just merged) at the
   start of a new review for the same profile.
5. Convert my standalone reproduction script into an automated regression
   test (e.g. using pytest) that fails on the current code and passes once
   the fix is in place.
### Inputs & outputs
 
- **Input:** two (or more) calls to `Orchestrator.run(profile_id, profile_data)`
  for the same `profile_id`, where `profile_data` may or may not have
  changed between calls.
- **Output (after fix):** each call to `run()` executes its planned tools
  fresh, so the returned `tool_results` always reflect the current
  `profile_data` and current external state, never a previous review's
  cached results.
### Risks & unknowns
 
- I don't yet know whether removing/scoping the cache will cause a
  performance regression (the cache may have been added intentionally to
  avoid redundant, costly calls like GitHub API requests within a single
  review). I need to make sure my fix only prevents cross-review staleness,
  not intra-review memoization of genuinely repeated calls.
- I haven't yet confirmed whether `Orchestrator` instances are created
  fresh per API request or reused as a long-lived singleton in production
  — `_run_agent_orchestration()` in `core/services/review_service.py` is
  currently a placeholder/stub and doesn't call the real `Orchestrator` at
  all, so I can't observe this directly from the live app yet. I'll need to
  ask in Slack or check with a mentor whether wiring up the real
  orchestrator is in scope for this issue or a separate concern.
- Unsure whether `SessionStore.set()`'s use of `session_state.update(results)`
  (merging old and new state) is itself intentional behavior I need to
  preserve for some other feature, or whether it's part of the bug.
### Edge cases
 
- A profile with no meaningful changes between reviews (should still behave
  correctly, i.e. no crash, even if the "fresh" result happens to match the
  old one).
- A profile where only some tools are affected by the update (e.g. resume
  text changed but GitHub repo didn't) — the fix shouldn't force unrelated,
  genuinely-unchanged tool calls to error out, just ensure they're not
  incorrectly cached long-term.
- Concurrent reviews for two different profiles happening at the same time
  should never share cached state with each other.
- A `SessionStore` that is unavailable/`None` (the code already supports
  this) should continue to work without crashing.
 