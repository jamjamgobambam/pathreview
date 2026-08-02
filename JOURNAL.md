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


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented everything but testing and adding edge cases. 

**Next steps:**
Testing, finding edge cases, and opening a PR. 

**Blockers:**
I didn't know about the pre-existing failures in make check before it was mentioned in the assignment. I definitely need to read everything before doing everything. But I will work on cleaning up at the end of the week.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]