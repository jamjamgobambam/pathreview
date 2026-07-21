## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/128)]

**Issue title:** [Add a dependency vulnerability scan to the CI pipeline]

**Tier:** A tier-3 issue

**Problem summary:**

We currently do not have any automated checks for security vulnerabilities in our Python or JavaScript dependencies. The goal is to integrate tools like pip-audit and npm audit into our CI pipelines so that any high-severity findings will cause the build to fail.

**Branch name:** [bug/128-add-vuln-scan-ci]

**Setup confirmation:** The App runs locally at localhost:5173

**Cohort ledger:** The issue is added to cohort ledger. 