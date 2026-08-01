# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a `has_tests` boolean to the repo analysis output

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

PathReview analyzes GitHub repositories, but it currently does not report whether a repository contains automated tests. This issue adds a `has_tests` Boolean field to the repository analysis output. The value should be `true` when the repository contains common testing indicators such as a `tests/` folder, a `test/` folder, `pytest.ini`, or files named like `test_*.py`. Otherwise, the value should be `false`.

**Branch name:** `feat/50-add-has-tests`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Is this issue right for me?

- The issue is labeled Tier 1 and is suitable for a first contribution.
- The task has a clear expected output: `has_tests` should be either `true` or `false`.
- The implementation mainly uses Python and GitHub repository file information.
- The issue is small enough to understand without changing the entire application.
- It will help me learn how an existing codebase analyzes repositories and returns structured results.
## Week 8 — Reproduction & solution planning

**Reproduction commit link:**  https://github.com/morishbhayani/pathreview/commit/ea215fe

**Reproduction summary:**

I ran `GitHubTool` against the PathReview repository, which contains automated tests. The tool successfully returned repository metadata including `has_readme`, but the returned data did not contain a `has_tests` field.

**PLAN.md link:** https://github.com/morishbhayani/pathreview/blob/feat/50-add-has-tests/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

I still need to determine the best GitHub API endpoint for retrieving the repository file tree and whether the existing test-detection logic in `ingestion/parsers/repo_analyzer.py` can be reused.

## Week 9 — Solution building & PR submission

### Check-in 1

**Current progress:**

I implemented repository test detection in `GitHubTool`. The tool now retrieves the repository tree from GitHub using the repository's default branch and adds a `has_tests` Boolean to the metadata output.

The detection returns `true` when it finds:

- a `tests/` directory
- a `test/` directory
- a `pytest.ini` file
- a Python file named `test_*.py`

It returns `false` when none of these indicators are present.

**Testing completed:**

- Added 9 focused unit tests in `tests/unit/test_github_tool.py`
- All 9 focused tests pass
- Ruff passes for both changed files
- Black passes for both changed files
- Mypy passes for both changed files
- A real GitHub smoke test against the PathReview repository returned `has_tests: True`
- Full unit suite result: 384 passed and 53 pre-existing failures
- Project lint result: 181 pre-existing errors, with no errors in the two files changed for this issue

**Implementation commit:**

https://github.com/morishbhayani/pathreview/commit/dfb7294

**Edge-case test commit:**

https://github.com/morishbhayani/pathreview/commit/5bd128f

**Current blockers:**

There are no blockers specific to issue #50. The repository still contains unrelated pre-existing unit-test and lint failures.

**Pull request:**

https://github.com/ascherj/pathreview/pull/527

**PR status:** Open and ready for review
