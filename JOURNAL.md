## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Scope-fit reasoning:**
I completed the “Is This Issue Right for Me?” checklist before selecting this issue. I can explain the requested change and its expected result: repository analysis currently lacks a direct test-presence signal, and the completed change should detect the listed test indicators and expose them as a `has_tests` boolean. I located and read the relevant repository-analysis code and its surrounding parser flow, reviewed the existing unit-test conventions, and can describe and test the intended before-and-after behavior. Tier 1 is a realistic fit because this is a self-contained enhancement rather than an architectural change. The estimated 2–4 hours of work is achievable before the Week 9 deadline. I also checked the issue comments and cohort ledger claim count and found no open blockers or unresolved dependencies that would prevent completion.

**Problem summary:**
The repo analysis output does not currently expose a simple signal for whether a submitted repository includes tests. Issue 50 asks for detection logic that checks common test indicators such as `tests/` or `test/` directories, `pytest.ini`, and Python test files named like `test_*.py`. A successful fix would add a `has_tests` boolean to the analysis output so reviewers can quickly identify whether a portfolio project demonstrates test coverage. This affects the agent repo-analysis flow, including the GitHub/repo analyzer tooling.

**Branch name:** feat/50-has-tests-repo-analysis

**Setup confirmation:** [x] App runs locally at localhost:5173; dependencies were installed and the application and tests ran successfully.

**Cohort ledger:** [x] Issue added to the cohort ledger on July 18, 2026.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [9dae6df — test: reproduce missing has_tests metadata](https://github.com/Yas7777/pathreview/commit/9dae6df99b1017ed15c6de4fb99a42283459f4c3)

**Reproduction summary:**
I reproduced the feature gap with a focused unit test that mocks a repository tree containing `tests/test_example.py`. `GitHubTool.execute()` succeeds, but accessing the expected `has_tests` output raises `KeyError` because the field is not produced.

**PLAN.md link:** [PLAN.md](https://github.com/Yas7777/pathreview/blob/feat/50-has-tests-repo-analysis/PLAN.md)

**Blockers or open questions:**
The issue references `agent/tools/repo_analyzer.py`, but that file is absent on this branch; the current path appears to be `agent/orchestrator.py` → `agent/tools/github_tool.py`. Maintainer guidance may also be needed on how to represent an unavailable or truncated Git tree without incorrectly returning `has_tests: false`.
