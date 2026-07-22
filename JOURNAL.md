## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/57
**Issue title:** Add a mock GitHub API server for integration tests

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The current codebase skip Github tool tests because they require live Github access. The goal is creating a mock Github server that answers with pre-saved fake data in order to run Github tool tests without sending requests to Github. This issue involves adding the Github tool tests (`tests/integration/test_github_tool.py`) and fixture responses (`tests/fixtures/github_responses/`) to the codebase.

**Branch name:** test/57-mock-github-server

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger