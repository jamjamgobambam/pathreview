## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The tech_detector.py script counts files in node_modules/ and build/ directories when analyzing a repository's primary language, causing incorrect language detection. A repo with 2 Python source files and 6 JavaScript files in node_modules gets detected as primarily JavaScript instead of Python. The fix should exclude vendored and build-output paths from the detection logic so only source code is counted.

**Branch name:** fix/tech-detector-vendored-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Is This Issue Right for Me?

### Part 1 — Understanding the Issue
- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- [x] Do I understand which part of the app is affected? The tech_detector.py module that analyzes repository language composition.
- [x] I can describe what "done" looks like: tech_detector.py excludes node_modules/ and build/ directories so language detection only counts actual source files.

### Part 2 — Tier Fit
- [x] Is the tier a realistic match for where I am right now? Yes, this is a Tier 1 fix (self-contained, single/few files, no cross-module understanding needed).

### Part 3 — Codebase Readiness
- [x] I've found and read the tech_detector.py file and understand the surrounding context.
- [x] I understand the code well enough to predict what a change will break.
- [x] I've found and read the test file (tests/unit/test_tech_detector.py) and understand existing tests.

### Part 4 — Scope and Time
- [x] How many others are already working on this issue? Checked — minimal claims on this issue.
- [x] Is the scope realistic for Weeks 8–9? Yes, estimated 3–6 hours for a Tier 1 fix.
- [x] This issue has no open blockers or dependencies on other unresolved issues.

### Verdict
Ready to proceed.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/solo6760/pathreview/commit/13a20bf5841f5d408be6e8f6729697543b42dead

**Reproduction summary:**
I reproduced the issue by running the unit tests `test_node_modules_excluded` and `test_build_directory_excluded` in `tests/unit/test_tech_detector.py`. Both tests failed because `TechDetector` does not exclude directories under skip patterns (like `/node_modules/` or `/build/`) when they appear at the start of relative file paths.

**PLAN.md link:** PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I normalized the file path separators and ensured relative paths start with a leading slash in `agent/tools/tech_detector.py`. This resolves the issue where directories like `node_modules/` or `build/` at the root were not matched against skip patterns.

**Next steps:**
Verify that the full suite of unit tests runs successfully, perform self-review checks, and submit the pull request.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/150-tech-detector-exclude-paths`

**What you built:**
I modified `TechDetector._should_skip_file` to replace backslashes with forward slashes and prepend a leading slash to the path before checking it against the skip patterns. This ensures directory patterns such as `/node_modules/` and `/build/` match correctly regardless of whether the path is absolute, relative, or Windows-based.

**Tests added or updated:**
No new tests were added as the existing failing tests in `tests/unit/test_tech_detector.py` (`test_node_modules_excluded` and `test_build_directory_excluded`) now pass successfully.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review has been received yet.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
I think the hardest aspect of this project for me was the fact that I had to read a lot of the documentation and codebase to understand the project before I could even think about fixing it. Even though I found the issue relatively easy to fix, it took me a while to get to that point as I had to read then test everything.

**What did you learn about working in a large codebase?**
I think the most important thing that I learned about working on this codebase is the importance of reading the docs first and testing the code. Another thing that I learned after working in such a big codebase was the imporance of being clear with your plan when submitting a PR. I think my PR was well documented and clearly stated what I did, however, it could've been better by adding more information

**How did AI tools help — and where did they fall short?**
AI tools really helped me summarize and understand what went wrong with the codebase. I found that using AI really sped up the process that would have otherwise taken me hours.

**What would you do differently if you started over?**
If I were to do this again, I would probably have picked a more complex issue so that I could learn and work more on the codebase. Even though a small fix can be make or break, I think it's less rewarding as I was able to finish everything very very quickly.

**What are you most proud of from this module?**
I think I'm most proud of the fact that I was able to contribute and fix something that will be used by others and the community. Working on this codebase really gave me the confidence to work on more complex issues and contribute to open source projects in the future.