## Solution plan

**Issue:** [Agent state isn't persisted across API restarts, causing in-progress reviews to be lost](https://github.com/ascherj/pathreview/issues/47)

### Understand
`Orchestrator.run()` accumulates tool results in memory and only calls `SessionStore.set()` after the entire plan finishes. Mid-run progress also lives in `ContextManager` (in-process only). If the process dies mid-loop, Redis has no checkpoint, and a restarted run rebuilds the plan and re-executes every tool from scratch — even though `session_store.get()` already runs at the start and is ignored for skip/resume.

**Expected:** After each completed tool (or equivalent step), session state is written to Redis; a restarted `run()` for the same `profile_id` skips finished tools and continues.

**Actual:** Redis is only updated at the end of a successful full run; a mid-run kill leaves `session:{profile_id}` empty and forces a full redo (confirmed via `scripts/repro_agent_state_persistence.py`).

### Map
| File | Role |
|---|---|
| `agent/orchestrator.py` | Main fix: checkpoint after each tool; resume/skip from loaded session |
| `agent/memory/session_store.py` | Redis get/set API (likely reuse as-is; maybe small helpers if needed) |
| `agent/memory/context_manager.py` | In-run memoization — decide whether to restore from Redis or keep process-local |
| `scripts/repro_agent_state_persistence.py` | Update to assert mid-run checkpoints + successful resume |
| `tests/unit/` (new or extended) | Unit tests for checkpoint + resume without needing a full UI review |

Optional later (out of core issue scope unless required for end-to-end): wire `review_service._run_agent_orchestration` to the real `Orchestrator` + `SessionStore` (today that path is stubbed).

### Plan
1. **Define session payload** — Store per-tool results under a stable key (e.g. tool name + input hash, or ordered plan step) so resume can tell “done” vs “pending.”
2. **Checkpoint mid-run** — In `Orchestrator.run()`, after each successful (and failed, if we want to record errors) tool, update `session_state` and call `session_store.set(profile_id, session_state)`.
3. **Resume on restart** — After `session_store.get()`, seed `results` from prior state and skip tools already completed before calling `_execute_tool`.
4. **Tests + repro** — Add unit tests (mock Redis or fake `SessionStore`) for: mid-run persist, no re-execution of completed tools, full completion still works. Update the repro script so the “kill mid-run” case leaves a partial Redis key and a second process continues from it.
5. **Verify** — Re-run repro against Redis; confirm kill leaves a checkpoint and resume does not redo finished tools.

### Inputs & outputs
**Inputs:** `profile_id`, `profile_data` (plan inputs), optional existing Redis session for that id, tool results as each step completes.

**Outputs / behavior change:** Redis `session:{profile_id}` updated throughout the run; `run()` return value still includes full `tool_results`; after a restart, completed steps are reused and only remaining tools execute.

### Risks & unknowns
- **Key identity:** Skipping by tool name alone is wrong if the same tool runs for multiple repos/inputs — need input hash (or step index) in the session schema.
- **Failed tools:** Whether to checkpoint failures and skip on resume, or retry them.
- **Stubbed review path:** UI/`process_review` still doesn’t call `Orchestrator`; agent-level fix solves #47 as stated in relevant files, but full product E2E won’t show it until wiring exists.
- **Partial ContextManager state:** Cache keys are in-memory; resume must not depend on them unless we also persist/restore that cache.

### Edge cases
- No `session_store` configured (current optional path) — behavior unchanged, no crash.
- Empty or corrupt Redis JSON — treat as no session and start fresh.
- Plan changes between runs (different tools/inputs) — only skip steps that still match; don’t apply stale results to new inputs.
- All tools already complete in Redis — `run()` should return restored results without re-executing.

