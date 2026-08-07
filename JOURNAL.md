**Issue link:** https://github.com/ascherj/pathreview/issues/121

**Issue title:** Write a contributor onboarding guide that walks through a complete issue → PR lifecycle

**Tier:** [ ] Tier 1  [ ] Tier 2  [*] Tier 3

**Problem summary:**
The issue requires a thorough understanding of the codebase and how each file interacts with the other to be able to write a comprehensive onboarding guide that helps a new contributor understand the code landscape and successfully get a PR submitted and merged.

**Branch name:** docs/121-contributor-onboarding-guide

**Setup confirmation:** [yes] App runs locally at localhost:5173

**Cohort ledger:** [yes] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [docs/121-contributor-onboarding-guide reproduction note](https://github.com/Morenayd/pathreview/commit/HEAD)

**Reproduction summary:**
This issue is a documentation-focused investigation of the repository structure and contributor workflow. The codebase review confirmed that the current guidance is dispersed across multiple docs and does not yet provide a single, end-to-end onboarding path for a new contributor.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:**
I am still working through how the API, agent, ingestion, and frontend components fit together so the onboarding guide can describe the project clearly without oversimplifying it.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I created a dedicated contributor onboarding guide and linked it from the main documentation entry points so new contributors can find a complete issue-to-PR walkthrough.

**Next steps:**
I am validating the documentation updates locally and preparing the pull request details and branch summary.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1002

**Branch:** `docs/121-contributor-onboarding-guide`

**What you built:**
I added a contributor-facing onboarding guide that explains how to choose an issue, set up the local environment, understand the repository layout, make a focused change, and prepare a pull request.

**Tests added or updated:**
No code tests were necessary for this documentation-only change.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Note: I ran both commands locally. The repository currently has existing lint and test failures outside this documentation-only change, so the self-review remains pending until those upstream issues are resolved.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
I did not receive reviewer feedback from the maintainers during this module, so I treated the process as a self-directed contribution and focused on making the documentation change clear, specific, and aligned with the repository's existing guidance.

**How you responded:**
I kept the scope focused on the onboarding gap, verified the branch and PR workflow locally, and documented the validation context in the PR description so reviewers would understand the documentation-only nature of the change.

---

### Reflection

**What was harder than you expected?**
The hardest part was not writing the guide itself, but understanding which parts of the repository were worth explaining in enough detail without overwhelming a first-time contributor. The codebase is broad, and the issue required translating that breadth into a concise, practical path from issue selection to PR submission.

**What did you learn about working in a large codebase?**
I learned that contributing to an existing production codebase is less about adding features quickly and more about fitting your work into established patterns, documentation, and review expectations. A useful contribution often depends on understanding the surrounding conventions as much as the specific feature or bug being addressed.

**How did AI tools help — and where did they fall short?**
AI tools helped me explore the repository quickly, summarize the existing docs, and draft the onboarding structure much faster than starting from scratch. Where they fell short was in making judgment calls about what should be included in the final guide; the real decisions still required me to read the repository context, compare the docs, and make sure the guidance reflected the project's actual workflow instead of just sounding polished.

**What would you do differently if you started over?**
I would spend a little more time early on mapping the docs and repo layout before drafting the guide, so I could make the structure more deliberate from the start. I would also start the PR process earlier so I could capture feedback sooner, even for a documentation change.

**What are you most proud of from this module?**
I am most proud of creating a contribution path that a new contributor can actually follow instead of just reading about abstract best practices. The guide turns the repository's existing setup and contribution process into a clearer end-to-end workflow.