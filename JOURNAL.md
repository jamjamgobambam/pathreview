## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug is that the agent keeps reusing old session data for the same user instead of treating each new review as a fresh analysis. In the current flow, the session cache in session_store.py and the orchestration logic in orchestrator.py can preserve stale tool results across reviews, so updates to a user’s portfolio are not fully reflected. A successful fix would ensure that previous review state is cleared or invalidated when a new review starts, allowing the agent to rerun the relevant tools and produce up-to-date results.

**Branch name:** fix/43-agent-session-state-not-cleared-between-reviews

**Setup confirmation:** [YES] App runs locally at localhost:5173

**Cohort ledger:** [YES] Issue added to cohort ledger