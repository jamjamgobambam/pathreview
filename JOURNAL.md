## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/43]

**Issue title:** [Agent session state is not cleared between reviews for the same user]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, session_store.py improperly caches agent state, causing the orchestrator to re-use stale tool outputs from prior sessions instead of fetching fresh data when a portfolio is updated. The, users who request follow-up reviews are served outdated information that ignores their recent changes. A successful fix will implement proper cache invalidation or session-aware state tracking so that portfolio updates force the orchestrator to re-run analysis tools. Ultimately, this ensures every review delivers accurate, real-time insights rather than recycled state.


**Branch name:** [fix/43-session-state-not-cleared]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
