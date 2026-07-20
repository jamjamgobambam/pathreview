## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This bug is about the AI reviewer "remembering" things it shouldn't. When a user asks for a review, the system saves the results from the tools it ran and links them to that user's ID so it can reuse them later. The problem is that this saved information never gets cleared out. So if a user updates their portfolio and asks for a second review, the system just reuses its old saved results instead of actually re-checking the new version of their portfolio. That means the user could get feedback about problems they already fixed, because the AI never really looked again. The fix needs to happen in agent/memory/session_store.py, the file responsible for storing this session information, by making sure it clears out old data before starting a new review.

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger