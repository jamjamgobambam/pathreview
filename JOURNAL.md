## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

Why? Because this is my first time, this was an issue I could be challenged yet understand by doing some deep diving. With the Scope of the project, I definitely need to focus on tier 1 issues.

**Problem summary:**
A bug is in the orchestrator.py file. Before running tools, it creates it's own session id from a user profile. So if the smae profile is reviewed again, the orchestrator starts from whatever session data was already stored for that profile instead of clearing it first. So although the new review creates a new session, the agent will still reuse the old per-profile session state unless that state is cleared.

To fix that, I would need to make sure the orchestrator will use the new session id instead to remove that stale tool. 

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue](https://github.com/Dani-risingBW/pathreview/commit/097b846a6f9928107e49848e8693a38695bca6a9)

**Reproduction summary:**
Ran a curl command to call POST/ reviews twice with the same profile_id. The second review reuses the same old state unless that state is cleared first. It returns the same message and response.

I also started a review of the same user but with two different resumes and the results were the exact same. They aren't supposed to be but with the agent reusing stale data it turns to be the same. 

**PLAN.md link:** [See the plan](pathreview\PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
None