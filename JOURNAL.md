## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a has_tests boolean to the repo analysis output
 #50


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The repository analysis tool currently provides metadata such as language, stars, forks, README availability, and topics, but it does not identify whether a repository contains automated tests. This missing capability prevents the analysis output from highlighting an important code quality indicator: test coverage presence. The fix will add detection logic in the repository analysis component to check for common testing indicators, including `tests/` or `test/` directories, `pytest.ini`, and Python test files matching the `test_*.py` pattern. The analysis output will expose this information through a new boolean field, `has_tests`, allowing users to quickly identify whether a repository includes tests.


**Branch name:** [feat/50-add-has-tests-to-repo-analysis]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Is This Issue Right for Me?

### Part 1 — Understanding the Issue

**Can I explain what this issue is asking for in my own words?**

Yes. This issue requires adding test detection capability to the GitHub repository metadata analysis tool. Currently, the `GitHubTool` collects repository information such as language, stars, forks, README availability, and topics, but it does not indicate whether a repository contains automated tests. The expected behavior is to add a new `has_tests` boolean field in the analysis output that identifies whether the repository contains common testing indicators such as a `tests/` or `test/` directory, a `pytest.ini` configuration file, or Python test files matching the `test_*.py` pattern.

**Do I understand which part of the app is affected?**

Yes. The affected code is located in the GitHub repository metadata tool. The main file I identified is the `GitHubTool` implementation, where repository metadata is collected in the `_fetch_repo_metadata()` method. The new detection logic will be added within this tool so that the analysis response includes the additional `has_tests` field.

**Do I understand what "done" looks like?**

Yes. Before the fix, the repository analysis output does not provide any information about testing support. After the fix, the output will include a `has_tests` boolean value:
- `true` when the repository contains test directories, pytest configuration, or matching test files.
- `false` when no test indicators are found.

---

### Part 2 — Tier Fit

**Is the tier a realistic match for where I am right now?**

Yes. This issue is a **Tier 1** issue because it is a localized change within a single tool file. The implementation does not require changes to multiple modules, database models, APIs, or system architecture. The scope is appropriate because it involves adding a small piece of repository metadata detection logic and exposing it in the existing analysis output.

---

### Part 3 — Codebase Readiness

**Can I find the relevant code?**

Yes. I located and reviewed the `agent/tools/github_tool.py`. The relevant section is the `_fetch_repo_metadata()` method, where the repository metadata dictionary is created and returned as the analysis output.

**Do I understand the surrounding code well enough to change it safely?**

Yes. The tool already follows a pattern where additional repository checks, such as `_has_readme()`, are implemented as helper methods and included in the metadata response. I can follow the same approach by adding a `_has_tests()` helper method and including its result in the metadata dictionary without affecting existing functionality.

**Have I read the relevant test file?**

There is currently no existing test file specifically covering the `GitHubTool` module. I have reviewed the implementation directly and understand the expected behavior. If tests are required, I will add coverage for the new `has_tests` detection logic separately.

---

### Part 4 — Scope and Time

**How many others are already working on this issue?**

I have checked the issue comments and tracker claims. I am comfortable proceeding with this issue.

**Is the scope realistic for Weeks 8–9?**

Yes. This is a Tier 1 feature addition with a limited scope. The expected work includes implementing the detection logic, updating the metadata output, and validating the behavior. The estimated effort is within the expected timeframe for a Tier 1 issue.

**Are there any blockers or dependencies?**

No. This issue has no known blockers or dependencies. The change can be completed within the existing GitHub metadata tool.

---

## Verdict

I am ready to claim this issue. It is a good fit because it is a focused Tier 1 change that improves the repository analysis output without requiring broad codebase changes. I have identified the affected code, understand the expected behavior, and can complete the implementation within the available timeframe.

## Week 8 — Reproduction & Solution Planning

**Reproduction commit link**

https://github.com/Sangeetha229/pathreview/commit/5bc6b6940c171679afb3db09b49867c620e76955

---

**Reproduction summary**

The issue was reproduced locally by adding a unit test in `tests/unit/test_github_tool.py` that validates the repository metadata output from `GitHubTool`.

The test confirmed that the current implementation does not include the expected `has_tests` boolean field in the repository analysis metadata. The existing metadata response contains fields such as `name`, `description`, `primary_language`, and `has_readme`, but test detection information is missing.

---

**PLAN.md link**

https://github.com/Sangeetha229/pathreview/blob/feat/50-add-has-tests-to-repo-analysis/PLAN.md

---

**Walkthrough video (recommended)**

https://www.loom.com/share/a85ab29d2c694b70992cfcabf61f98fd

---

**Blockers or open questions**

- Need to confirm the best approach for detecting tests using GitHub API repository tree data while minimizing additional API requests.
- Need to determine the expected fallback behavior if GitHub API calls fail due to rate limits, permissions, or network errors.
- Need to validate whether `has_tests` detection should support only common patterns (`tests/`, `test/`, `pytest.ini`, `test_*.py`) or include additional conventions such as `spec/` and `__tests__/`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

- Implemented the `_get_repo_tree()` helper in `agent/tools/github_tool.py` to retrieve repository file structure using the GitHub Tree API with a single request.
- Added the `_has_tests()` helper method to detect common test indicators:
  - `tests/` and `test/` directories
  - `test_*.py` and `*_test.py` file patterns
  - pytest configuration files
- Integrated the new `has_tests` boolean field into the repository metadata output in `_fetch_repo_metadata()`.
- Followed the existing `_has_readme()` pattern by adding error handling and returning `False` safely when GitHub API requests fail.
- Updated `tests/unit/test_github_tool.py` with tests covering:
  - repositories containing tests
  - repositories without tests
  - API failure fallback behavior


**Next steps:**
- Run validation commands:
  - `make check`
  - `make test-unit`
- Review the implementation for edge cases such as empty repositories and large repository tree responses.
- Update PR description with implementation details, testing instructions, and reviewer notes.
- Submit the pull request and verify that the PR template is fully completed.

**Blockers:**
- None.
---