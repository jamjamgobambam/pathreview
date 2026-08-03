## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/57
**Issue title:** Add a mock GitHub API server for integration tests

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The current codebase skip Github tool tests because they require live Github access. The goal is creating a mock Github server that answers with pre-saved fake data in order to run Github tool tests without sending requests to Github. This issue involves adding the Github tool tests (`tests/integration/test_github_tool.py`) and fixture responses (`tests/fixtures/github_responses/`) to the codebase.

**Branch name:** test/57-mock-github-server

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/xxy361/pathreview/commit/7bc126023c004fe8894f0c7c103efb56c1a44f0a

**Reproduction summary:**
Since the issue is on creating tests for GitHub tools, I focused on understanding the existing implementation for GitHub tools (`agent\tools\github_tool.py`), particularly looking at the try-and-except blocks to see what errors are expected. The docstrings are very helpful for understanding the functions, as well as inputs/outputs.

**PLAN.md link:** https://github.com/xxy361/pathreview/blob/test/57-mock-github-server/PLAN.md

**Walkthrough video (recommended):** 
N/A

**Blockers or open questions:**
N/A


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have not implemented anything so far. None of the sub-tasks from PLAN.md are done.

**Next steps:**
Implement the solutions, document the implementation, and submit a PR.

**Blockers:**
N/A

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `test/57-mock-github-server`

**What you built:**
Added a mock-GitHub-API integration test suite for `GitHubTool` using `pytest-httpserver`, so the tool's GitHub interactions can be tested without live GitHub access. Each test points `tool.base_url` at a local mock server that answers repo-metadata and README requests with pre-saved JSON fixtures.

**Tests added or updated:**
`tests/integration/test_github_tool.py` (9 tests) covering the success path with full metadata, null/missing-field fallbacks, README present/absent detection, and error mapping for 404 (not found), 403 (rate limited), and generic 500 responses, plus missing-argument validation. Also added fixture responses under `tests/fixtures/github_responses/` (`repo_success.json`, `repo_nulls.json`, `error_403.json`, `error_404.json`, `error_500.json`).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]