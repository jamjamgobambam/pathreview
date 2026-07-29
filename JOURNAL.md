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