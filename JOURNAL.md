## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
A bug is in the orchestrator.py file. Before running tools, it creates it's own session id from a user profile. So if the smae profile is reviewed again, the orchestrator starts from whatever session data was already stored for that profile instead of clearing it first. So although the new review creates a new session, the agent will still reuse the old per-profile session state unless that state is cleared.

To fix that, I would need to make sure the orchestrator will use the new session id instead to remove that stale tool. 

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger