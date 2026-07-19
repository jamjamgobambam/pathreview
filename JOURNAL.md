## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Scope-fit reasoning:**
 I can explain the requested change and its expected result: repository analysis currently lacks a direct test-presence signal, and the completed change should detect the listed test indicators and expose them as a `has_tests` boolean. I located and read the relevant repository-analysis code and its surrounding parser flow, reviewed the existing unit-test conventions, and can describe and test the intended before-and-after behavior. I prefer to work on a Tier 1 issue as this is a self-contained enhancement rather than a architectural change. I also checked the issue comments and cohort ledger claim count, and found no open blockers or unresolved dependencies that would prevent completion. I analysed the “Is This Issue Right for Me?” checklist before selecting this issue.

**Problem summary:**
The repo analysis output does not currently expose a simple signal for whether a submitted repository includes tests. Issue 50 asks for detection logic that checks common test indicators such as `tests/` or `test/` directories, `pytest.ini`, and Python test files named like `test_*.py`. A successful fix would add a `has_tests` boolean to the analysis output so reviewers can quickly identify whether a portfolio project demonstrates test coverage. This affects the agent repo-analysis flow, including the GitHub/repo analyzer tooling.

**Branch name:** feat/50-has-tests-repo-analysis

**Setup confirmation:** [x] App runs locally at localhost:5173; dependencies were installed and the application and tests ran successfully.

**Cohort ledger:** [x] Issue added to the cohort ledger on July 18, 2026.
