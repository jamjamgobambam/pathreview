## Week 7 — Issue selection

**Issue link:** [Issue #43](https://github.com/ascherj/pathreview/issues/43)

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview stores agent session data in Redis through `agent/memory/session_store.py`, and the issue reports that the stored state can carry over when the same user requests another portfolio review. If the user updates their portfolio, stale results from the earlier review may be reused instead of every relevant tool analyzing the new information. The session store is connected to the review workflow in `agent/orchestrator.py`, so the fix will need to ensure that cached state is scoped to one review or cleared at the correct point in the workflow. A successful fix will make a second review use the updated portfolio data and will include tests proving that results from the first review do not leak into it.

**Is this right for me?:**
1. I can explain the issues in my own words
2. This is my first open source contribution. So I'm choosing Tier 1.
3. I have found and read the relevant code and test file
4. The scope is realistic, and I'm fine with others working on this as well

All boxes checked!

**Branch name:** `fix/43-clear-agent-session`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
