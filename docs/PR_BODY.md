## Summary
Persists agent session state to Redis after each tool step so long-running reviews survive API/process restarts. Previously, `Orchestrator.run()` only wrote to Redis after the full plan finished, so a mid-run kill lost all progress and forced a full redo.

## Issue
Closes #47

## Changes
- Checkpoint each completed tool result to Redis in `Orchestrator.run()` (keyed by `tool_name:input_hash`)
- On restart, load the session and skip already-finished steps
- Add `SessionStoreProtocol` so the orchestrator can use Redis or an in-memory fake store
- Add `tests/unit/test_agent_state_persistence.py` (checkpoint, resume, full skip, failures, no-store path)
- Update `scripts/repro_agent_state_persistence.py` to verify mid-run checkpoints + resume against Redis
- Document reproduction and plan in `docs/JOURNAL.md` / `docs/PLAN.md`

## Testing
- [ ] Unit tests pass (`make test-unit`) — full suite has pre-existing failures; issue #47 tests pass (`pytest tests/unit/test_agent_state_persistence.py`)
- [ ] Integration tests pass (`make test-integration`)
- [ ] Linter passes (`make lint`) — repo-wide pre-existing failures; changed files pass
- [ ] Type checker passes (`make typecheck`) — repo-wide pre-existing stub/numpy issues; changed agent files pass
- [x] New/updated tests cover the changes
- Verified with: `python scripts/repro_agent_state_persistence.py` → `FIX VERIFIED` (partial Redis checkpoint after kill; resume skips finished tools)

## Screenshots / Demo
N/A — agent/Redis behavior; repro script output shows mid-run checkpoint + resume skip.

## Notes for Reviewers
- Core change is in `agent/orchestrator.py`: `SessionStore.set()` moves from end-of-run into the per-tool loop, with resume via step keys.
- Failed tools are also checkpointed and skipped on resume (no automatic retry).
- UI/`process_review` still uses a stubbed agent path; this fixes the agent-level persistence called out in #47 (`orchestrator.py` / session memory). Wiring the real orchestrator into the review service is out of scope here.
