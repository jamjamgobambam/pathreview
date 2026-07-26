## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This bug is about the AI reviewer "remembering" things it shouldn't. When a user asks for a review, the system saves the results from the tools it ran and links them to that user's ID so it can reuse them later. The problem is that this saved information never gets cleared out. So if a user updates their portfolio and asks for a second review, the system just reuses its old saved results instead of actually re-checking the new version of their portfolio. That means the user could get feedback about problems they already fixed, because the AI never really looked again. The fix needs to happen in agent/memory/session_store.py, the file responsible for storing this session information, by making sure it clears out old data before starting a new review.

**Selection notes:** I chose this as a Tier 1 issue since it's my first time contributing to a large codebase, and a single-file, well-scoped bug felt like the right level of difficulty to start with. Before committing, I checked the issue comments and the cohort ledger — a couple of other students had also expressed interest in this issue, but the assignment clarified that claims are non-exclusive, so I was comfortable moving forward. The estimated 3–4 hours fits well within my available time before the Week 9 deadline given my other coursework, and there were no blockers or dependencies noted on the issue.

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rehanNY06/pathreview-RB/commit/302e4de

**Reproduction summary:**
I wrote a standalone script that creates an Orchestrator with a fake tool that counts how many times it actually runs, then calls `.run()` twice for the same profile. The logs confirmed a "tool_result_cache_hit" on the second call, and the tool only executed once across both calls — proving the second review silently reused the first review's cached result instead of running fresh.

**PLAN.md link:** https://github.com/rehanNY06/pathreview-RB/blob/fix/43-agent-session-state-not-cleared/PLAN.md

**Walkthrough video (recommended):** (skipped, optional)

**Blockers or open questions:**
The real orchestration logic isn't wired into the live API yet — `_run_agent_orchestration()` in `review_service.py` is currently a placeholder that returns hardcoded data. I reproduced the bug directly against the `Orchestrator` class instead. I'm not yet sure if wiring the real orchestrator into the API is in scope for my fix, or a separate issue — planning to ask in Slack/office hours.