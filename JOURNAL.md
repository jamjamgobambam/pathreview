## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Selection notes:**
I selected issue #47 as a Tier 3 issue because I wanted to push past a beginner-level fix and take on a challenging problem like agent state persistence across restarts. This problem touches concurrency, idempotency, and system reliability, which are skills I want to build.

**Problem summary:**
When the agent processes a review, its progress lives only in memory: `agent/orchestrator.py` runs through a plan of tool calls (GitHub analysis, tech detection, README scoring, skill extraction, etc.), and `agent/memory/context_manager.py` caches each tool's output as it goes, but none of this is written to Redis until the entire plan finishes. If the API server restarts partway through, everything completed up to that point is discarded, since there's no partial state saved anywhere durable. A successful fix would save the orchestrator's progress to Redis after each tool step completes rather than only at the end, and on restart, check that saved state to skip steps already done instead of re-running them, while making sure a crash mid-save can't leave the stored state half-written or inconsistent.

**Branch name:** fix/47-agent-state-not-persisted-on-restart

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger