# Module 3 Progress Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Long-running reviews that span five or more repositories currently lose all progress when the server restarts because agent session data is stored only in memory. When the API process terminates (during maintenance or deployment), all in-flight review state is lost with no way to recover. The fix requires persisting the agent's memory context to Redis before shutdown and restoring it on startup. This will ensure that users don't lose progress on long-running reviews and allow the system to handle server restarts gracefully without data loss.

**Issue fit and selection reasoning:**

**Scope-fit checklist:**
- [x] Bounded fix — Not a massive refactor; adds persistence layer to `ContextManager` and `SessionStore`
- [x] 3-4 week scope — Confirmed as Tier 3; estimate 2 weeks of work (session serialization, caching logic, tests)
- [x] Clear acceptance criteria — Cache survives restart; tool results re-used from Redis, not re-executed
- [x] Affects real users — Long-running reviews that span repositories lose progress on deploy
- [x] Active maintenance — Issue shows maintainer engagement and clear reproduction steps
- [x] Specific files identified — `Orchestrator`, `ContextManager`, `SessionStore`, Redis connection

**Why this is Tier 3 for me:**
- Requires understanding of async orchestration and memoization patterns (learning goal: multi-step system architecture)
- Involves Redis persistence and serialization — new domain to me (learning goal: state management across system restarts)
- Builds on existing `SessionStore` patterns — familiar enough to avoid being overwhelming
- Clear deliverable: cache the tool results, persist to Redis, restore on restart
- No language barriers (Python expertise) or missing infrastructure

**Branch name:** fix/47-persist-agent-state-across-restarts

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [9500b94](https://github.com/peter-abj/pathreview/commit/9500b94)

**Reproduction summary:**
Created unit tests demonstrating that `ContextManager` results are lost when the Orchestrator is re-initialized, simulating an API restart. Showed that while `SessionStore` can persist session state to Redis, the in-memory cache is not synchronized with Redis, causing tool re-execution on restart instead of cache hits.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** [Not recorded]

**Blockers or open questions:**
- Need to investigate what ToolResult objects contain to determine JSON serializability
- Uncertain whether profile_id includes user context to prevent cache collisions
- Should cache key use profile_id or review_id for multi-review scenarios?

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Working through PLAN.md. Confirmed the Week 8 open questions: tool results are
`ToolResult` dataclasses, so they serialize cleanly with `dataclasses.asdict`.
Sub-tasks 1–3 are done — `ContextManager` now has `to_dict`/`from_dict`,
`SessionStore` has `get_cache`/`set_cache` under a separate `cache:` key, and the
orchestrator restores the cache at the start of `run()`.

**Next steps:**
Add checkpointing after each tool so a mid-review restart keeps partial progress,
then write tests covering the serialization round trip and a full restart. Run
`make check` and `make test-unit` and open a draft PR for peer feedback.

**Blockers:**
None. Decided to key the cache on `profile_id` (matching how `SessionStore`
already keys sessions) instead of `review_id`; noted as a follow-up if concurrent
reviews on one profile ever need isolation.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/275

**Branch:** `fix/47-persist-agent-state-across-restarts`

**What you built:**
The orchestrator's memoized tool-result cache is now persisted to Redis so an API
restart no longer wipes an in-progress review. `ContextManager` serializes its
cache to a JSON-safe form, `SessionStore` stores it under a separate `cache:` key,
and the orchestrator restores it on the next run and checkpoints after every tool
so partial progress survives a mid-review restart.

**Tests added or updated:**
`tests/unit/test_agent_state_persistence.py` — 10 tests covering the serialization
round trip (including `ToolResult` reconstruction and skipping unserializable
entries), the `SessionStore` cache read/write, and an end-to-end restart where a
second orchestrator reuses the persisted cache instead of re-running the tool.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

_Pre-existing failures: on this branch `make test-unit` reports 53 failing tests
and `make check` reports pre-existing ruff/mypy errors (e.g. missing library stubs,
`agent/tools/market_analyzer.py`) that exist on a clean checkout and are unrelated
to this issue. My changes introduce no new failures — the count is 53 before and
after, my 10 new tests all pass, and mypy/ruff/black are clean on every file I
touched (enforced by the pre-commit hook)._

**Draft PR feedback received from:** none yet (draft opened for peer review )

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [•] No — still awaiting review

**Summary of feedback:**
No review came in

[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
The complexity of the architecture and how different pieces each play a different role. II had to study each file to understand the logic and that took some time 

**What did you learn about working in a large codebase?**
It’s so much fun working in a codebase because the organization of logic is really fascinating and collaboration itself is enjoyable

**How did AI tools help — and where did they fall short?**
I used Claude Code to deeply understand the codebase and how each piece fits into the puzzle. I also used it for debugging and understanding error messages

**What would you do differently if you started over?**
I wouldn’t change anything. The experience itself, to me, was very fruitful. 
**What are you most proud of from this module?**
It was my first time navigating through a monolithic codebase and so, having to contribute in a manner like I would in an industry setting was very fulfilling for me.
