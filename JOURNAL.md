## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/50

**Issue title:** Add a has_tests boolean to the repo analysis output

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Test coverage is important, adding detection logic to check if a repo has test files/folders or a pytest.ini,etc. A successful fix would give a boolean output - true or false for the test checks. Relevant files for the implementation would be agent/tools/github_tool.py and agent/tools/repo_analyzer.py

**Branch name:** test/50-add-boolean-for-test

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue selection reasoning:**
1. Can I explain what this issue is asking for in my own words?
        [x] *I can explain the problem and the expected behavior in 2–3 sentences without reading the issue*

2. Do I understand which part of the app is affected?
        [x] *I've located the relevant files and confirmed they exist in the codebase*

3. Do I understand what "done" looks like?
        [x] *I can describe a concrete before-and-after: what the user sees before the fix and what they see after.*
    
4. Is the tier a realistic match for where I am right now?
    *This is my first open source contribution, therefore I am choosing tier-1 for starters*




## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [[link to commit documenting the reproduced issue]](https://github.com/Nishanth-Raju/pathreview/commits/test/50-add-boolean-for-test/)

**Reproduction summary:**
Setup the whole project in docker and ran the project using "make run" and it did not run the project as intended at first. Then had to troubleshoot for a bit and got it to run. There was no detection logic for the project to find test/ or tests/ folder.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** No video was recorded

**Blockers or open questions:**
The issue calls for two relevant files:
agent/tools/github_tool.py
agent/tools/repo_analyzer.py

but the project only has the first one and not the repo_analyzer.py


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

- [x] Added `has_tests` field to metadata dictionary in `_fetch_repo_metadata` method
- [x] Implemented `_has_tests()` method that checks for common test patterns via GitHub API
- [x] Integrated test detection logic following the same pattern as existing `_has_readme()` method

**Next steps:**

- Run tests to verify the implementation works correctly
- Test with actual GitHub repositories to confirm detection accuracy
- Submit PR once tests pass

**Blockers:**

None - discovered that repo_analyzer.py actually exists in ingestion/parsers/ directory (not in agent/tools/ as mentioned in the issue). The implementation in github_tool.py directly detects tests via GitHub API which is more reliable.

---

### Check-in 2 (end of week)

**PR link:** [To be submitted]

**Branch:** `test/50-add-boolean-for-test`

**What you built:**
Added test detection logic to the GitHub tool that returns a `has_tests` boolean in the repository metadata. The implementation checks for common test patterns (test/, tests/, pytest.ini, setup.cfg, tox.ini) using GitHub API HEAD requests. The method gracefully handles API errors and returns False if no test indicators are found.

**Tests added or updated:**
Relevant unit tests present and passing — documented in Check-in 2. The test suite validates the `_has_tests()` method's ability to detect common test patterns (test/, tests/, pytest.ini, setup.cfg, tox.ini) via GitHub API calls. Tests confirm the method returns True when test indicators are found and False when none are present.

**Self-review confirmation:** [x] Code follows existing patterns  [x] Proper error handling included  [x] Integrates with existing tool structure

**Draft PR feedback received from:** None yet - ready for community review





## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
 No review came in.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Organizing the tasks and planning was the hardest.

**What did you learn about working in a large codebase?**
Read, Read, Read. Knowing the code base and the whats and whys is very important.

**How did AI tools help — and where did they fall short?**
Helped me a lot while going through the codebase. But fell short when I have to prioritize things out.

**What would you do differently if you started over?**
Might pick a different/harder issue to work with.

**What are you most proud of from this module?**
Able to handle a big codebase.