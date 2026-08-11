## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Multi-repo reviews that take a long time (5+ repositories) can lose all progress if the API server restarts mid-run. Session state for an in-flight review lives only in process memory and is not persisted to Redis until the job finishes. After a restart, that memory is gone, so the review cannot continue and users have to start over. A successful fix would checkpoint agent session state to Redis during the run so reviews survive restarts and can continue from where they left off.

**Branch name:** `fix/agent-state-persistence`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/JaredAung/pathreview/commit/38b192d362a2f6a4e597fddc266ed7a2c1d0b8f7

**Reproduction summary:**
I reproduced the bug with `scripts/repro_agent_state_persistence.py`, which runs `Orchestrator` against Redis with slow mock tools and kills the process mid-plan. After the kill, Redis had no `session:repro-issue-47` key, and a fresh re-run executed every tool again from scratch — confirming mid-run progress lives only in memory and is not checkpointed to `SessionStore` until `run()` finishes.

**PLAN.md link:** https://github.com/JaredAung/pathreview/blob/fix/agent-state-persistence/docs/PLAN.md

**Blockers or open questions:**
N/A

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented mid-run Redis checkpointing and resume in `Orchestrator.run()` (`agent/orchestrator.py`): after each tool, session state is written under a `tool_name:input_hash` key, and a restarted run skips completed steps. Added `tests/unit/test_agent_state_persistence.py` (6 tests) and updated `scripts/repro_agent_state_persistence.py` to verify partial checkpoints + resume against Redis. PLAN.md items 1–4 are done; verified via unit tests and the repro script (`FIX VERIFIED`).

**Next steps:**
Open a draft PR from `fix/agent-state-persistence`, run full `make check` / `make test-unit`, and solicit draft PR feedback.

**Blockers:**
No blockers.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/841

**Branch:** `fix/agent-state-persistence`

**What you built:**
`Orchestrator.run()` now checkpoints each completed tool result to Redis immediately (keyed by tool name + input hash) instead of only at the end of the plan. On restart, it loads that session and skips already-finished steps so the review continues from the last checkpoint.

**Tests added or updated:**
`tests/unit/test_agent_state_persistence.py` — covers checkpoint-after-each-tool, resume skip, full-session no re-execution, no-store path, failed-tool checkpointing, and step-key input hashing. Also updated `scripts/repro_agent_state_persistence.py` as an end-to-end Redis verification of the fix.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Note: Full `make check` / `make test-unit` fail on pre-existing repo issues unrelated to this PR. Issue #47 coverage passes via `pytest tests/unit/test_agent_state_persistence.py` (6/6) and `python scripts/repro_agent_state_persistence.py` (`FIX VERIFIED`).

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviews yet.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Recreating the bug was the hardest since there was no obvious way to simulate a mid-crash. So I had to write a dedicated script.

**What did you learn about working in a large codebase?**
It is harder to work with codebases that I didn't develop from scratch. It takes time to understand design decisions and how everything ties together.

**How did AI tools help — and where did they fall short?**
Used Claude to design the script and explain the problem.

**What would you do differently if you started over?**
Better planning would have reduced the time taken to finish each part.

**What are you most proud of from this module?**
The simulation script would be the part that I am most proud of since it surfaces the issue as well as sets up a foundation to test success on.
