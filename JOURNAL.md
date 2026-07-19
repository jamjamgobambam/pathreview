## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The repo analysis output does not currently expose a simple signal for whether a submitted repository includes tests. Issue 50 asks for detection logic that checks common test indicators such as `tests/` or `test/` directories, `pytest.ini`, and Python test files named like `test_*.py`. A successful fix would add a `has_tests` boolean to the analysis output so reviewers can quickly identify whether a portfolio project demonstrates test coverage. This affects the agent repo-analysis flow, including the GitHub/repo analyzer tooling.

**Branch name:** feat/50-has-tests-repo-analysis

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
