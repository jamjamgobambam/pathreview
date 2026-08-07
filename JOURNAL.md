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