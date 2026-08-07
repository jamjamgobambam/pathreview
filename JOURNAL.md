# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview’s technology detector is supposed to ignore dependency and generated-output directories when determining a repository’s programming languages. However, its current skip patterns contain leading slashes, so root-level paths such as `node_modules/package/index.js` and `build/bundle.js` are not excluded. As a result, vendored or generated JavaScript files can affect language detection and cause the repository’s primary language to be reported incorrectly. A successful fix will make the filtering logic work for both root-level and nested directories while passing the existing unit tests.

**Selection notes — “Is this issue right for me?” checklist:**

- The expected behavior and current failure are clearly explained.
- The issue includes a reproducible example and identifies relevant failing tests.
- The likely scope is limited to `agent/tools/tech_detector.py` and `tests/unit/test_tech_detector.py`.
- The issue does not require a database migration, external API integration, or major frontend changes.
- I have experience with Python, backend development, file-processing logic, and unit testing.
- I understand the likely cause: root-level paths do not contain the leading slash used by the existing skip patterns.
- I will verify root-level paths, nested paths, and path separators without changing unrelated detection behavior.
- This Tier 1 issue has a realistic scope for my first contribution to this repository.

**Branch name:** `fix/150-ignore-vendored-build-files`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tungnguyenasu/pathreview/commit/41585836d39f3b4ee72b42d29cfb09bf8bff9d6d

**Reproduction summary:**
I reproduced Issue #150 by running the existing `test_node_modules_excluded`
and `test_build_directory_excluded` unit tests. Both tests failed because
root-level `node_modules/` and `build/` paths were not filtered, allowing
JavaScript files in those directories to make JavaScript the reported primary
language instead of Python.

**PLAN.md link:** https://github.com/tungnguyenasu/pathreview/blob/fix/150-ignore-vendored-build-files/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I need to verify whether path component comparisons should be case-sensitive.
I will also confirm that normalizing Windows backslashes does not change
existing behavior for repository paths that already use forward slashes.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced Issue #150, traced the problem to the leading-slash substring
patterns in `TechDetector._should_skip_file()`, and completed the solution
plan. I also identified the existing tests that need stronger assertions and
the edge cases that require regression coverage.

**Next steps:**
I will normalize path separators, compare exact directory components, add
regression tests, run the targeted and complete test suites, and open a draft
pull request for feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/585

**Branch:** `fix/150-ignore-vendored-build-files`

**What you built:**
I updated `TechDetector` to normalize repository paths and ignore exact
dependency, vendor, cache, virtual-environment, and generated-output directory
components. The fix works for root-level, nested, and Windows-style paths
without excluding similarly named legitimate directories.

**Tests added or updated:**
I updated `tests/unit/test_tech_detector.py` to strengthen the existing
`node_modules`, `vendor`, and `build` tests. I also added regression coverage
for nested ignored directories, Windows separators, ignored configuration
files, similarly named valid directories, and inputs where every file is
excluded. The full `tests/unit/test_tech_detector.py` file passes (32 tests).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

*Note:* Both boxes are left unchecked because the repository has pre-existing,
unrelated failures on `main`: `make test-unit` reports 51 failing tests in
other modules (unchanged by this branch), and `make check` fails on pre-existing
`ruff`/`black`/`mypy` findings in files this change does not touch. The tests
specific to Issue #150 all pass, and `mypy` reports no issues on
`agent/tools/tech_detector.py`.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback has been received on the pull request. For
Summer 2026, formal reviewer feedback is not part of the course workflow, so I
am documenting that the PR is still awaiting review and moving forward with the
reflection.

**How you responded:**
No response or additional code changes were required because no reviewer
feedback was received.

---

### Reflection

**What was harder than you expected?**

The most difficult part of this contribution was not the final code change
itself, but getting from an unfamiliar issue to a reliable local development
and testing workflow. Setting up the project on Windows required working
through Docker, WSL, Git Bash, Python environments, and the project's `make`
commands. I also had to distinguish failures caused by my issue from failures
that already existed elsewhere in the repository. Once I reached the actual
bug, the code change was relatively small, but proving the root cause and
testing it carefully took more work than I initially expected.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase requires much more
attention to scope than building a project from scratch. I could not simply
change the behavior until my example worked; I had to trace how
`TechDetector._should_skip_file()` was used, understand the existing test
patterns, preserve the public output format, and avoid changing unrelated
behavior. I also learned the importance of separating pre-existing failures
from failures introduced by my branch. In my own projects I can often change
multiple related pieces at once, but in an open-source contribution a smaller,
well-tested change is easier to review and safer to merge.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for navigating the unfamiliar repository, explaining
error messages, identifying likely files involved in the issue, and helping me
turn the issue description into a structured reproduction and solution plan.
They were also useful for suggesting edge cases such as root-level paths,
nested paths, Windows backslashes, and similarly named directories like
`rebuild` or `vendor_tools`.

However, I still had to verify the suggestions against the actual PathReview
code and tests. Some commands depended on whether I was using PowerShell or Git
Bash, and an AI-generated command that was valid in one shell could fail in the
other. I also had to run the test suite myself to determine which failures were
pre-existing. This showed me that AI can accelerate investigation and suggest
solutions, but it cannot replace checking the repository's real behavior and
development environment.

**What would you do differently if you started over?**

I would spend more time at the beginning verifying the full development
environment and the repository's baseline test status before starting the issue
work. I would also use Git Bash consistently for the project's `make` workflow
instead of switching between PowerShell and Git Bash. For the contribution
itself, I would record the baseline `make check` and `make test-unit` results
immediately so that later I could compare them directly against my branch.

I would still choose a Tier 1 issue for a first contribution because the
smaller scope allowed me to focus on the contribution workflow instead of
being overwhelmed by a large feature. After completing one issue like this, I
would feel more comfortable choosing a higher-tier issue next time.

**What are you most proud of from this module?**

I am most proud that I did more than make the two originally failing tests
pass. I traced the problem to the path-matching logic and implemented the fix
in a way that handles root-level paths, nested paths, and Windows-style path
separators while avoiding false matches on legitimate directories. I also
expanded the tests to cover those edge cases and confirmed that the complete
`test_tech_detector.py` suite passes with 32 tests. The process gave me
experience following an issue from selection and reproduction through planning,
implementation, testing, and a real pull request.