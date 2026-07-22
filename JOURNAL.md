## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The orchestrator caches agent state by user ID inside `agent/memory/session_store.py`. When a user submits a second portfolio review after updating their portfolio, the system reuses the cached tool results from their previous session instead of re-running the tools against the new portfolio data. This means the review a user receives can be based on stale information rather than what they actually just submitted. A successful fix would ensure each new review request triggers fresh tool execution (or properly invalidates/clears the cached session state) so results always reflect the current portfolio.

**Branch name:** fix/43-clear-session-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger