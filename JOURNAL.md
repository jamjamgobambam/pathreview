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
