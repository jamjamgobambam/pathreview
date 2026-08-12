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

**PR link:** https://github.com/ascherj/pathreview/pull/966#issue-5067937138

**Branch:** `test/57-mock-github-server`

**What you built:**
Added a mock-GitHub-API integration test suite for `GitHubTool` using `pytest-httpserver`, so the tool's GitHub interactions can be tested without live GitHub access. Each test points `tool.base_url` at a local mock server that answers repo-metadata and README requests with pre-saved JSON fixtures.

**Tests added or updated:**
`tests/integration/test_github_tool.py` (9 tests) covering the success path with full metadata, null/missing-field fallbacks, README present/absent detection, and error mapping for 404 (not found), 403 (rate limited), and generic 500 responses, plus missing-argument validation. Also added fixture responses under `tests/fixtures/github_responses/` (`repo_success.json`, `repo_nulls.json`, `error_403.json`, `error_404.json`, `error_500.json`).

**Self-review confirmation:** [] make check passes  [] make test-unit passes
Note: There are pre-existing failures in unit tests before the fix of this issue (53 failed, 384 passed). This number didn't change after the fix of this issue. `make check` also have pre-existing failures. To ensure that linter and typecheck pass for the code files touched by the fix, the following commands were ran on to achieve the same effect:
- `.venv/Scripts/ruff.exe check tests/integration/test_github_tool.py`
- `.venv/Scripts/black.exe tests/integration/test_github_tool.py`
- `.venv/Scripts/mypy.exe tests/integration/test_github_tool.py`
- `.venv/Scripts/ruff.exe check agent/tools/github_tool.py`
- `.venv/Scripts/black.exe agent/tools/github_tool.py`
- `.venv/Scripts/mypy.exe agent/tools/github_tool.py`

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Passing the checks was the most surprising piece. I did not expect to encounter type check error during committing. I got an error that was "returning any from function declared to return "bool" from the `github_tool.py`. Even though I didn't touch the production code in that file, but the type error was still caught. Everything else went smoother than expected. 

**What did you learn about working in a large codebase?**
If one thing I learned, I would say reading the docs before working on the code. Especially, the doc on architecture helped understanding how directories are organized in the codebase, which helped me understand what parts of the codebase might be relevant to the issue. This is different from my own project, because for my own projects I know how things are organized and where to look for things. In a large codebase that has many files, I think understanding the organization of the directories is part of understanding the architecture.

**How did AI tools help — and where did they fall short?**
AI was the most useful when there are errors show up, particularly when involving the `make` commands (the setup and `make check`) and in general anything with the command lines. I also personally find AI to be useful when "double checking" the work. Sometimes I manually implemented or wrote things, then asked AI what could be alternatives or what were things not covered, I found AI very useful, even sometimes more useful than generating things from zero. I think AI does a good job implementing things based on existing plan, but when I tried to use it for the planning phase, I found myself often need to modify manually or go through many rounds back and forth.

**What would you do differently if you started over?**
I think I might choose an issue that is not about writing tests, but actually fix some logic or implement some features - something that is slightly less isolated with the existing code. 

**What are you most proud of from this module?**
Getting through the whole workflow was great, and organizing the commit history to be clean to look at was very satisfying.