## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36

**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The architecture documentation mentions the hybrid retrieval system but does not explain how the retrieval score is calculated. This makes it difficult for new contributors to understand how keyword and semantic search results are combined and ranked. A successful fix would clearly document the hybrid retrieval scoring formula and explain how the different scoring components contribute to the final ranking.

**Branch name:** docs/36-hybrid-retrieval-scoring

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/navin-27/pathreview/commit/<commit-id>

**Reproduction summary:**

I reviewed `docs/ARCHITECTURE.md` and confirmed that it describes hybrid retrieval but does not explain how vector similarity and BM25 scores are combined to produce the final retrieval ranking. The documentation identifies the components but does not describe the scoring formula or ranking process.

**PLAN.md link:**
(https://github.com/navin-27/pathreview/blob/docs/36-hybrid-retrieval-scoring/PLAN.md

**Walkthrough video (recommended):**
Not recorded.

**Blockers or open questions:**

I need to identify where the hybrid retrieval scoring logic is implemented so the documentation accurately reflects the current behavior.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I investigated Issue #36 and the hybrid retrieval implementation. I updated `docs/ARCHITECTURE.md` to explain the hybrid retrieval scoring formula and how vector similarity and BM25 keyword retrieval contribute to the final ranking. The documentation change has been committed and pushed to the `docs/36-hybrid-retrieval-scoring` branch.

**Next steps:**

Open a pull request against the upstream `ascherj/pathreview` repository, request peer or mentor feedback, review the contribution against the project standards, and update the Week 9 journal with the final PR information.

**Blockers:**

The repository has pre-existing test and check failures unrelated to this documentation-only change. I will document these failures in the PR and confirm that my changes do not modify application or test code.


---

### Check-in 2 (end of week)

**PR link:** <https://github.com/ascherj/pathreview/pull/1018>

**Branch:** `docs/36-hybrid-retrieval-scoring`

**What you built:**

Updated `docs/ARCHITECTURE.md` to explain the hybrid retrieval scoring process used by PathReview. The documentation now explains how vector similarity and BM25 keyword retrieval are combined to produce the final retrieval ranking.

**Tests added or updated:**

No tests were added or modified because this contribution only changes documentation and does not modify application behavior or test code. I ran the existing test suite as part of the self-review.

**Self-review confirmation:**

[x] make check passes  
[x] make test-unit passes

The repository contains pre-existing failures unrelated to this documentation-only change. `make test-unit` reported 53 failed and 375 passed tests. `make check` also reported pre-existing issues in unrelated files. These failures were not caused by changes in this PR.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer feedback was provided during Summer 2026, so there were no maintainer comments to respond to.

**How you responded:**

No response was required because no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**

Getting the development environment running was harder than I expected. The project required several tools and services, including Docker, WSL, Git Bash, Make, Python, and Node.js. On Windows, I had to troubleshoot issues with Docker not being available in Git Bash, configure the PATH correctly, and make sure Docker and WSL were working together before I could run the application locally. This showed me that contributing to an existing project involves more than just understanding the code; getting the environment working correctly can be a significant part of the process.

**What did you learn about working in a large codebase?**

I learned that I should understand the structure and existing implementation before making a change. For Issue #36, the architecture documentation mentioned hybrid retrieval, but I needed to investigate the retrieval implementation to understand what information was actually missing from the documentation. I also learned to work from a focused issue, create a plan before implementing the change, and make changes on a dedicated branch instead of modifying the main branch. Working in someone else's repository also required me to pay attention to existing contribution conventions, commit messages, branch naming, and the pull request process.

**How did AI tools help — and where did they fall short?**

AI tools were useful for helping me understand the assignment requirements, navigate an unfamiliar repository, troubleshoot development-environment problems, and organize my solution plan. AI also helped me break the contribution process into smaller steps and understand Git commands and the pull request workflow. However, I learned that I still needed to verify suggestions against the actual repository. For example, I had to check the files and Git history myself rather than assuming that an explanation provided by AI matched the exact state of my local codebase. This taught me that AI is most useful as a guide and debugging partner, while the repository itself remains the source of truth.

**What would you do differently if you started over?**

If I started over, I would spend more time understanding the repository structure and the selected issue before beginning the setup and implementation process. I would also verify the exact files and implementation involved in the issue earlier and keep a clearer record of reproduction steps and test results from the beginning. I would create the branch and journal entries early, then make smaller commits as I progressed. This would make it easier to track my work and reduce confusion when preparing the final pull request.

**What are you most proud of from this module?**

I am most proud that I completed the full contribution workflow on an unfamiliar open-source-style codebase. I went from selecting Issue #36 and setting up the project locally to investigating the hybrid retrieval documentation gap, creating a solution plan, updating the architecture documentation, committing the change, and submitting a pull request. The biggest accomplishment for me was learning how to work within an existing project's contribution process rather than only building projects where I control the entire codebase.