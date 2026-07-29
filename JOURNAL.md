# PathReview — Module 3 Journal

Running record of progress across Weeks 7–10.

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/128

**Issue title:** Add a dependency vulnerability scan to the CI pipeline

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

PathReview currently runs lint, typecheck, unit, integration, and frontend tests in GitHub Actions, but nothing checks whether installed Python or JavaScript dependencies contain known security vulnerabilities. That means a dependency with a published CVE could ship without CI noticing. The fix adds automated scanning to `.github/workflows/ci.yml`: `pip audit` for Python dependencies (after installing the project with dev extras) and `npm audit` for the frontend (after `npm ci`), failing the build when high-severity findings are detected. This is DevOps/CI work rather than application logic, but it directly improves the project's security posture and gives contributors faster feedback on risky dependency updates.

**Branch name:** `chore/128-add-dependency-vulnerability-scans`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue claim comment:** https://github.com/ascherj/pathreview/issues/128#issuecomment-5034547950

**Cohort ledger entry:** Yie Sheng Chen · `speculaas` · #128 · [cohort spreadsheet](https://docs.google.com/spreadsheets/d/1oclK-70-klhGofiaw6krk8-zV_wZiumsR-Xnd_l5ZR8/edit?gid=1079392097#gid=1079392097)

### "Is this right for me?" checklist reasoning

| Question | Assessment |
|---|---|
| **Is it actually open?** | Yes — listed in the open issue export and issue tracker with no linked merged PR. |
| **Is the scope clear?** | Yes — add `pip audit` and `npm audit` to CI, fail on high-severity findings, primary file is `ci.yml`. |
| **Is it the right size?** | Tier 3, estimated 3–5 hours. Larger than Tier 1, but bounded to one workflow file plus policy decisions. |
| **Is the maintainer active?** | Yes — upstream repo has recent merges and active issue activity. |
| **Does it match my skill level?** | Chosen deliberately to learn CI/GitHub Actions YAML. I accept the Tier 3 scope because my primary goal is DevOps/CI experience, not the fastest Tier 1 PR. |

**Scope reasoning:** I considered Tier 1 alternatives (#37 snapshot tests, #159 structlog/caplog) for lower risk, but selected #128 because it is the most direct path to editing GitHub Actions workflows, configuring audit tools, and iterating through the CI feedback loop. Main risks: existing dependencies may already have advisories, Python and npm audit tools differ in severity filtering, and policy choices (blocking threshold, job structure) need investigation before the PR is merge-ready.

**Supporting reference:** See `docs/issue-128-context.md` for Mermaid diagrams, CI design notes, and implementation roadmap from issue-selection discussions.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/speculaas/pathreview/commit/474ab43e5c8060948355504d054e8bee3aac25e5

**Reproduction summary:**
Issue #128 is a missing CI security gate rather than a runtime app bug. I reproduced it by inspecting `.github/workflows/ci.yml` on `main`: the workflow has lint, typecheck, unit, integration, and frontend jobs only — no `pip audit`, `npm audit`, or any vulnerability-scan step. Search for those terms returns no matches, which matches the issue’s claim that Python and JavaScript dependencies are not automatically audited. Full notes are in `docs/reproduction-128.md` on that commit.

**PLAN.md link:** https://github.com/speculaas/pathreview/blob/chore/128-add-dependency-vulnerability-scans/PLAN.md

**Walkthrough video (recommended):** *(optional — not recorded yet; not graded)*

**Blockers or open questions:**
- Will existing dependencies already fail `pip audit` / `npm audit --audit-level=high` on first enablement?
- Should Python use plain `pip audit` (any finding fails) or a pinned tool with severity filtering to mirror npm’s high/critical policy?
- Is documenting local `make audit` / SETUP commands in-scope for the PR, or should the first PR touch only `ci.yml`?

---

## Week 9 — Implementation and PR

*(To be filled in next week.)*

---

## Week 10 — Iteration and reflection

*(To be filled in next week.)*
