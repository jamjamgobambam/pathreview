## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
When a user wants a new review, the previous session cache is not cleared. This means that a new review is going to take consideration of the previous session, even though it has nothing to do with it. Inside "agent/memory/session_store.py", there should be some error or missing functionality to clear the session state.

**Branch name:** [paste branch name here]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger