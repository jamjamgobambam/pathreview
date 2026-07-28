## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/128)]

**Issue title:** [Add a dependency vulnerability scan to the CI pipeline]

**Tier:** A tier-3 issue

**Problem summary:**

We currently do not have any automated checks for security vulnerabilities in our Python or JavaScript dependencies. The goal is to integrate tools like pip-audit and npm audit into our CI pipelines so that any high-severity findings will cause the build to fail.

**Branch name:** [bug/128-add-vuln-scan-ci]

**Setup confirmation:** The App runs locally at localhost:5173

**Cohort ledger:** The issue is added to cohort ledger.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [e8b038e](https://github.com/J321A/pathreview/commit/e8b038e4f9f4159025daf2f712abef02af8d00d7)

**Reproduction summary:**
Confirmed `.github/workflows/ci.yml` has no dependency vulnerability scan (no `pip-audit`, no `npm audit`) across any of its five jobs. Running the tools locally proved the gap matters: `npm audit` reported 11 vulnerabilities in the frontend (1 critical, 5 high — e.g. `ws`, `react-router`) and `pip-audit` reported 2 in Python deps (`chromadb`, `ecdsa`) — 13 total that currently pass CI undetected. Full log: [docs/reproduction-128.md](docs/reproduction-128.md).

**PLAN.md link:** [PLAN.md](https://github.com/J321A/pathreview/blob/bug/128-add-vuln-scan-ci/PLAN.md)

**Walkthrough video (recommended):** _(not yet recorded)_

**Blockers or open questions:**
Whether maintainers prefer a separate `security-scan` CI job or added steps in existing jobs; and how to handle the 13 pre-existing findings so enabling the gate doesn't red-light every open PR (fix-first vs. a reviewed ignore-list at the `high` threshold).
