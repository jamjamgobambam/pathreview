# Solution plan

**Issue:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost
https://github.com/ascherj/pathreview/issues/47

## Understand

The orchestrator runs a plan of tools (GitHub analysis, tech detection,
README scoring, skill extraction, market analysis) for a profile review.
Every completed tool result lives only in a plain dict inside
`ContextManager` in process memory. The Redis-backed `SessionStore` is
written exactly once, at the very end of `Orchestrator.run()`, after the
whole plan finishes.

Expected behavior: if the API restarts while a review is running,
re-running that profile should pick up from the last completed tool.
Actual behavior: the restart wipes the in-memory dict, the final
`session_store.set()` never ran, so Redis holds nothing and the review
recomputes every tool from scratch. I confirmed this locally with
`scripts/reproduce_issue_47.py` (see `docs/issue-47-reproduction.md`):
two tools completed, the store was empty at crash time, and both tools
executed a second time after the simulated restart.

Root cause: persistence happens once at run completion instead of
incrementally as each tool finishes, and nothing rehydrates the context
cache on startup.

## Map

* `agent/memory/context_manager.py`. `ContextManager.store_tool_result()`
  and `get_tool_result()` are the memoization layer. This is where
  write-through persistence and startup rehydration belong.
* `agent/orchestrator.py`. `Orchestrator.run()` owns the tool loop and the
  single end-of-run `session_store.set()` call. Needs per-tool
  checkpointing and needs to construct a session-scoped context manager.
* `agent/memory/session_store.py`. Existing Redis wrapper with
  `get`/`set`/`delete` and a JSON serialization boundary plus a default
  1 hour TTL. Reused as-is, but its constraints shape the design.
* `agent/tools/base.py`. `ToolResult` dataclass that has to survive a JSON
  round trip through Redis.
* `tests/unit/test_agent_state_persistence.py` (new). Restart-simulation
  tests using an in-memory fake of `SessionStore`.
* `scripts/reproduce_issue_47.py` (new). Reproduction and verification
  script that runs against both the broken and fixed code.

## Plan

1. Extend `ContextManager` to optionally take a `session_store` and a
   `session_id`. On every `store_tool_result()`, write the full cache
   through to Redis under a session-scoped key
   (`session:<profile_id>:context`). On construction, load that key and
   rehydrate the in-memory dict so a fresh process starts with the
   completed results.
2. Add serialization helpers in `context_manager.py` that convert
   `ToolResult` objects to and from plain JSON dicts (tagged so they
   deserialize back into `ToolResult`), and skip values that are not JSON
   serializable without failing the run.
3. Update `Orchestrator.run()` to build the session-scoped
   `ContextManager` when a store is present, and checkpoint session state
   after every tool instead of only at completion, including an
   `_in_progress` marker with `completed_steps`, `total_steps`, and
   partial results.
4. On successful completion, write the final results, remove the
   `_in_progress` marker, and clear the per-session context key so a
   finished review does not leave stale checkpoint data behind.
5. Add `tests/unit/test_agent_state_persistence.py` covering write-through,
   rehydration after a simulated restart, session isolation, and the
   non-serializable case, then verify end to end with
   `scripts/reproduce_issue_47.py` on both branches and run the full
   suite with `pytest tests/ -v`.

## Inputs & outputs

Inputs: the fix consumes the same `profile_id` and `profile_data` that
`Orchestrator.run()` already takes, plus the existing `SessionStore`
instance. `ContextManager.__init__` gains two optional parameters
(`session_store`, `session_id`), so all existing no-argument call sites
keep working.

Outputs: the return value of `run()` is unchanged. What changes is the
persistence behavior. Redis now holds a `session:<profile_id>:context` key
with serialized tool results that is updated after every tool, and the
`session:<profile_id>` session entry gains a temporary `_in_progress`
field while a run is active. After a restart, re-running the same profile
produces cache hits for completed tools (observable as
`context_hydrated` and `tool_result_cache_hit` log events) instead of
re-executing them.

## Risks & unknowns

* Serialization. `ToolResult` is a Python dataclass and Redis stores JSON
  strings. Tool `data` payloads could contain values `json.dumps` rejects.
  If a bad payload makes `store_tool_result()` raise, persistence would
  break the very runs it is supposed to protect, so the write-through in
  `context_manager.py` has to skip unserializable entries and log instead
  of raising.
* TTL expiry. `session_store.py` defaults to a 3600 second TTL. A long
  multi-repository review that stalls near the hour mark could have its
  checkpoint expire between crash and re-run. I need to decide whether the
  context key needs a longer TTL than regular session data.
* Key collisions. The API layer also stores session data through
  `SessionStore` under `session:<id>` keys. I need to check the routes in
  `api/` that read session state to make sure the new
  `session:<profile_id>:context` key and the `_in_progress` field do not
  confuse any existing reader.
* Write amplification. Writing the whole context dict to Redis after every
  tool is O(results) per tool. Fine at the current plan size of about 5
  tools, but worth a note in the code if plans grow.
* Redis outages. If Redis is down mid-run, the checkpoint writes will
  fail. `session_store.set()` already catches and logs its own errors, so
  runs degrade to the old in-memory behavior, and I need a test proving
  that path stays non-fatal.

## Edge cases

* A tool result whose payload is not JSON serializable: the run must still
  complete, the value stays usable in the in-memory cache for the current
  process, and only the persisted copy is skipped.
* Restart while a tool is mid-execution: only tools that fully completed
  are resumed from checkpoint; the interrupted tool re-runs from scratch
  rather than resuming half-done work.
* Two different profiles running tools with identical inputs: results are
  keyed per session, so profile A's checkpoint must never satisfy a cache
  lookup for profile B.
* Re-running a profile after a fully successful run: the completion path
  cleared the checkpoint, so the re-run executes fresh instead of serving
  a stale `_in_progress` state.
* Redis unavailable at checkpoint time: the run finishes anyway with
  in-memory results, and the failure is logged rather than raised.

## Week 9 resolutions

How each open risk landed once the implementation was finished.

* **TTL expiry: resolved by giving the context key its own TTL.**
  `CONTEXT_TTL_SECONDS` in `context_manager.py` is 24 hours, passed
  explicitly on every `_persist()` write, so a checkpoint outlives the
  1 hour default that regular session data uses. A crash and recovery that
  takes longer than an hour still resumes.
* **Key collisions: resolved, no reader is affected.** I grepped `api/` and
  `core/` for `SessionStore` and `session_store` and found no call sites at
  all. The orchestrator is not wired into any route yet in this repo, so
  nothing outside `agent/` reads these keys. The `:context` suffix also
  keeps the new key in its own namespace, and `_in_progress` is removed
  from the session entry on the completion path before the final write.
* **Serialization: resolved as planned.** `_serialize()` returns `None` for
  anything `json.dumps` rejects, the entry is skipped and logged rather
  than raised, and the in-memory cache keeps the value for the current
  process. Covered by
  `test_non_serializable_result_is_skipped_without_error`.
* **Redis outages: resolved and now tested.** Three tests drive a real
  `SessionStore` wrapping a Redis client that raises `ConnectionError`, and
  assert that hydration, write-through, and a full orchestrator run each
  degrade to in-memory behavior instead of failing.
* **Write amplification: accepted, not addressed.** Persisting the whole
  cache after each tool is still O(results) per tool. At the current plan
  size of about 5 tools this is a handful of small writes, so I left it
  alone rather than adding incremental-write complexity to a fix that is
  about correctness. If plans grow, `_persist()` is the single place to
  change.

One edge case surfaced during implementation that was not in the original
plan: the context key could hold something other than a dict, either from a
partial write or from a future writer reusing the namespace. `_hydrate()`
now type-checks the payload and starts the session cold instead of raising
on startup.
