## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/57

**Issue title:** Add a mock GitHub API server for integration tests

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
AI Agent tests are skipping GitHub tooling tests because live API access is required. To get around this limitation, a mock API server needs to be setup. Files to setup: 
tests/integration/test_github_tool.py
tests/fixtures/github_responses/

Success will have tests for the GitHub server work with a mock server. 
**Branch name:** [paste branch name here]

**Setup confirmation:** [x] App runs locally at localhost:5173
(Linux only, Windows still having some issues.)
**Cohort ledger:** [x] Issue added to cohort ledger

**Issue Fit and Selection**
I have worked with multple interlinked systems before and can intergrate them toegeher. I have also setup mock API servers and can get pytests to run with them. I am okay with the 3-4 others working on the issue and estimate I can complete before week 9.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bmurdata/pathreview/commit/290d79d1d9283261bfac60cae988131be5d3dd22

**Reproduction summary:**
Issue is that the tests do not account for GitHub tests locally. 
I verified that no such tests exist in the codebase, and none were found in the tests folder or subfolders.
The agent also has tools for GitHub that are not tested.
I plan to add intergration tests and fixtures accordingly.

**PLAN.md link:** https://github.com/bmurdata/pathreview/blob/test/57-add-mock-GitHub-test-API/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
HTTP Server intergration and exactly how to replicate the calls for GitHub mock server API.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the conftest to make the API server.
**Next steps:**
Implement the tests and testing framework using pytest httpserver.
**Blockers:**
Claude often hallucinates requirements or gives non functional code requiring review and patches to pass linters. I am also limited by knowledge of HTTPserver in pytest

---
### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1023

**Branch:** `test/57-add-mock-GitHub-test-API`

**What you built:**
Built a mock GitHub server API in conftest that calls the GitHub tool. The tool uses pytest HTTPServer to mock a GitHub server called by the tool in conftest and fixture_resolver. To get the responses, the fixture_resolver is called rathet than storing responses in GitHib_responses.
**Tests added or updated:**
To pass linter tests, tests/conftest.py and agent/tools/github_tool.py were modified. I also added a fixture_resolver to get fixtures and return a response.
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** None
## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in
**How you responded:**


---

### Reflection

**What was harder than you expected?**
Getting the system to work as designed was an issue. I had to use a Ubuntu virtual machine in order to make the application run. 

I also was surprised by ruff, black, and mypy code checkers before commits. I spent a lot of time making sure the code would pass the linters.

Finally, Claude helped a lot but also introduced new problems. Prompts would ignore linters or use placeholders I had not intended. 

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
When building your own codebase you learn a little of everything. Even if the project becomes large, it is normally easy to get back up to speed quickly. When working on someone else's code, you don't have that same familiarity. So, you have to spend more time identifying where an issue could be coming from. then finding the issue and then applying a fix.

**How did AI tools help — and where did they fall short?**
I used Claude to help me get a basic HTTP server up and running and asked for help on how it would work. It was good, but it did not fix or find linting errors that came up during commits. It also left a lot of placeholders, and had to be prompted repeatedly to use what was already in the project instead of installing new modules.

For example, it wanted to test Flask and ran it itself, but claimed it could not do the same for pytest. This may be why the code needed constant revision.

**What would you do differently if you started over?**
I would have selected a more narrow issue, and taken more steps to get the app working before selection. Even after getting it up, the app would still have issues I wasnt familar with in the testing and linting, so I had to spend a long time fixing it.

**What are you most proud of from this module?**
Creating a real pull request and getting a feel for larger codebases using AI.
