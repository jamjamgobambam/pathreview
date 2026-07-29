## Solution plan

**Issue:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost — https://github.com/ascherj/pathreview/issues/47

### Understand

`Orchestrator.run()` (`agent/orchestrator.py:31-76`) executes a review as a sequential loop over a list of tool calls (e.g. `github_tool`, `tech_detector`, `readme_scorer`, `skill_extractor`, `market_analyzer`). Each tool's result is accumulated in a local `results` dict and also cached in `ContextManager.results` (`agent/memory/context_manager.py:15`) — both plain in-process Python dicts with no durable backing. The only write to Redis happens once, after the entire loop finishes (`agent/orchestrator.py:65-67`).

**Expected behavior:** if the API server restarts while a review is partway through its tool plan, the review should be resumable — already-completed tool results should be checkpointed durably, and restarting should skip re-running those steps.

**Actual behavior (confirmed via local reproduction, see `scripts/repro_issue47.py`):** killing the process mid-plan leaves Redis with nothing at all for that profile, even though some tools already succeeded. On the next run, every tool re-executes from the beginning — there is no notion of "already done" to check against.

**Root cause:** persistence is an all-or-nothing operation tied to full-plan completion, not an incremental per-step checkpoint. `ContextManager` provides memoization only within a single process's lifetime; it has no Redis/disk backing at all.

### Map

Files I expect to touch:
- `agent/orchestrator.py` — `run()` (where/when persistence happens), `_execute_tool()` (where each tool's result becomes available and could be checkpointed)
- `agent/memory/context_manager.py` — `ContextManager` (currently in-memory only; needs to either gain durable backing or be replaced as the source of truth by `session_state`)
- `agent/memory/session_store.py` — `SessionStore.get/set/delete` (Redis key format `session:{id}`, `ttl_seconds=3600` default); note `set()` currently swallows all exceptions and only logs (`session_store.py:65-66`) — a checkpoint write that silently fails would defeat the fix
- `scripts/repro_issue47.py`, `scripts/repro_issue47_worker.py` — existing reproduction, will double as a regression check
- Likely new: `tests/unit/test_orchestrator_checkpointing.py` (no orchestrator tests exist today)

Out of scope for this issue, but noted as related debt: `core/services/review_service.py:process_review` has an analogous gap — it only writes `Review.status` to Postgres at start (`"processing"`) and end (`"complete"`/`"failed"`), with no per-stage checkpoint between ingestion/orchestration/RAG/safety-check. Also, `Orchestrator` currently has no callers anywhere in the codebase (`_run_agent_orchestration` in `review_service.py` is a hardcoded stub) — see Risks below.

### Plan

1. Add a per-step checkpoint: inside the `for tool_name, tool_input in plan` loop in `run()`, call `session_store.set(...)` immediately after each tool's result is computed, not only after the loop exits.
2. Track completion explicitly: persist a `completed_steps` (or similar) structure alongside `tool_results` in the session state, keyed by `tool_name` + `ContextManager.hash_input(tool_input)`, so a resumed run can tell "done" from "not yet attempted" for the exact same input.
3. Make plan execution resumable: when `run()` loads `session_state` at the top (`orchestrator.py:47-49`), check each planned step against `completed_steps` before calling `_execute_tool()`, and skip steps whose result is already checkpointed for that exact input hash.
4. Make checkpoint writes safe to interrupt: ensure a crash during a Redis write can't leave `session_state` half-updated — write the full updated state in one atomic `SETEX` call (the current `SessionStore.set()` already does this per-call), and decide how to surface/retry a failed checkpoint write instead of silently swallowing it (`session_store.py:65-66`).
5. Add a regression test that: runs a fixed multi-step plan, hard-kills the process partway through (reusing the pattern in `scripts/repro_issue47_worker.py`), restarts, and asserts the previously-completed step is not re-executed and the final result matches an uninterrupted run.

### Inputs & outputs

- **Input:** unchanged — `Orchestrator.run(profile_id: str, profile_data: dict)`.
- **New output/side effect:** `session_store` now receives a write after every individual tool step, not just once at the end; the persisted `session_state` gains a marker of which `(tool_name, input_hash)` pairs are complete.
- **On resume:** calling `run()` again with the same `profile_id` after an interruption should read the checkpointed state, skip already-completed steps, and produce the same final `tool_results` as an uninterrupted run would have.

### Risks & unknowns

- `SessionStore.set()` catches all exceptions and only logs (`session_store.py:65-66`) — today, a failed checkpoint write fails silently. Adding more frequent writes without addressing this means checkpoint failures could go unnoticed, undermining the whole fix. Need to decide whether to raise, retry, or surface this differently.
- `Orchestrator` is not currently wired into the live app — `core/services/review_service.py:_run_agent_orchestration` is a hardcoded placeholder stub and never imports `agent.orchestrator` (confirmed via repo-wide grep: zero callers of `Orchestrator(`). Fixing `Orchestrator`'s persistence alone won't change production behavior until/unless it's wired into `process_review`. Need to confirm with mentors whether wiring it in is part of this issue's scope or a separate follow-up.
- Default Redis TTL is 3600s (`session_store.py:56`). A long review that pauses between checkpoints for longer than an hour could have earlier partial state expire before it resumes. Need to decide whether each incremental checkpoint should refresh the TTL.
- No existing tests cover `orchestrator.py`, `context_manager.py`, or `session_store.py` — test scaffolding (fake tools, real or fake Redis) has to be built essentially from scratch; `scripts/repro_issue47.py` is the only precedent so far.
- Multiple workers/processes checkpointing the same `profile_id` concurrently could race on the same Redis key (read-modify-write on `session_state` isn't currently atomic across the get/set pair) — unclear yet whether this is a realistic scenario for this codebase's deployment model.

### Edge cases

- Process crashes before the very first tool in the plan runs (no checkpoint exists yet) — resume must behave like a fresh run, not error on a missing/empty session state.
- Process crashes during or immediately after the very last tool, before the (to-be-removed) final `session_store.set()` — once checkpointing is per-step, this should resolve naturally, but needs a test to confirm the last step's checkpoint and the "plan complete" marker land correctly.
- The same `tool_name` is requested again with different `tool_input` after a restart (e.g. `profile_data` changed between the interrupted and resumed run) — the skip-if-already-done check must key off `tool_name` + `input_hash` together (matching how `ContextManager.hash_input` already works), not `tool_name` alone, or a stale result could be returned for changed input.
- A tool that eventually succeeded after internal retries (`retry_with_backoff` in `agent/error_handling.py`) — the checkpoint must store only the final successful result, not an intermediate failed attempt.
- Redis temporarily unreachable during a checkpoint write — must not silently proceed as though the checkpoint succeeded (see Risks above); needs explicit handling rather than the current swallow-and-log behavior.
