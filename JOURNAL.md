## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/52

**Issue title:** Add a contribution_streak field to the GitHub analysis (longest consecutive days of commits) #52

**Tier:** [ ] Tier 1  [✓] Tier 2  [ ] Tier 3

**Problem summary:**
This issue is looking to implement a new feature for the users. It looks at the GitHub contribution history of the user and finds the largest streak and displays it to the user, which is what a successful implementation would look like. This is mainly done with the GitHub API and the code is located in agents/tools/github_tool.py. The `contribution_streak` is currenty missing, which should show the commit streak from GitHub activity and post the streak as a new field in the analysis output to show as a portfolio signal.

**Branch name:** feat/52-github-streak-tracker

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger

**Selection notes:**
I'm comfortable working in Python and API integration, but this would be my first time implementing something into a larger codebase with multiple features and services. The issue 52 is a Tier 2 issue, scoped into a single tool file in `agent/tools/github_tool.py` with a clear success in adding a `contribution_streak`. The 4-6 hour estimate shoudl be accurate for implementation and API work alongside setup.


## Week 8 - Reproduction and Fix Plan

**Reproduction steps:**
1. 1. Ran `GitHubTool().execute({"github_username": "octocat", "repo_name": "Hello-World"})`
2. Tool returned success=True with metadata keys: name, description, primary_language, star_count, fork_count, open_issues_count, last_commit_date, has_readme, topics, homepage
3. `contribution_streak` was absent which confirms the feature gap described in issue #52

**Reproduction commit link:**
https://github.com/RTailor2301/pathreview/commit/0ec579c

**Reproduction summary:**
Ran `GitHubTool.execute()` locally with `github_username=octocat` and `repo_name=Hello-World`. The tool returned repo metadata successfully (star_count, last_commit_date, etc.) but the output dict did not contain `contribution_streak`. Also added a unit test in `tests/unit/test_github_tool.py` that asserts the field exists; it fails, confirming the feature gap in `agent/tools/github_tool.py`

**PLAN.md link:** https://github.com/RTailor2301/pathreview/blob/feat/52-github-streak-tracker/PLAN.md

**Blockers or open questions:**
Should `contribution_streak` be computed from commits in the specific repo passed to the tool, or from the user's overall GitHub contribution calendar across all repos? I plan to start with repo-scoped commits as a start.

## Week 9 - Solution building and PR

**Progress:**
Implemented PLAN.md tasks 1-4, adding `_fetch_commit_dates()` to pull commit dates from the GitHub commits API, `_calculate_longest_streak()` to find the longest consecutive-day run, and wired `contribution_streak` into `_fetch_repo_metadata()`. Added error handling so commit fetch failures return streak 0 without breaking the tool, then opened a draft PR on GitHub.

**Next steps:**
Finish unit tests (task 5), run self-review checks on my changed files, address draft PR feedback, and mark PR ready for review. No current blockers.

**PR Link:** https://github.com/ascherj/pathreview/pull/835

**Branch:** `feat/52-github-streak-tracker`

**What was built:**
Added a `contribution_streak` field to `GitHubTool` that fetches commit history for the given repo, finds the longest run of consecutive calendar days with at least one commit, and includes that integer in the metadata dict returned by `execute()`. If the commits API fails, the tool still returns repo metadata with `contribution_streak` set to 0.

**Additional tesets:**
Updated `tests/unit/test_github_tool.py` with 8 tests covering: `contribution_streak` present in output, streak calculation for consecutive/non-consecutive/single-day/empty inputs, same-day deduplication, empty commit history returning 0, and API error fallback returning 0 while keeping other metadata.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in yet.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part of the whole process to me was understanding the codebase. The implementation and tests were not as hard as once you understand the entire system, you can effectively prompt any AI for implementation. However, the most important part, and also hardest, was fully understanding how each part of the system worked in terms of structure and how the tests were run so I could write my own.

**What did you learn about working in a large codebase?**
One thing I learned about working in a large codebase was the conventions used. There were strict rules about spacing and types for each of the files which needed to be followed, and I always ran into problems with the linter due to my spacing habits. Even the commits needed a structured message, which I thought was interesting as in my own projects I didn't really follow a convention.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for helping with implementation once I figured out exactly how the system worked. However, it fell short when trying to understand the codebase as it is, since there are so many files and different parts of issues that the context window would fill up quickly. I had to run through the different systems myself and understand my issue in its entirety before relying too much on AI.

**What would you do differently if you started over?**
If I had to start over, I would keep most things the same except to read over the contribution rules more carefully, as well as following the conventions better. Most times I ran into issues, it was due to having small spacing errors which were caught before being pushed and not including types or other return values in the documentation of a function. Overall, I would try to fully understand these conventions before starting if I had to start over.

**What are you most proud of from this module?**
One thing I'm most proud of throughout this module was my ability to sort out issues as they came. For example, if I ran into a linter issue, I would be able to solve it on my own after getting used to the conventions and not need to heavily rely on AI tools. The same went for understanding how the different parts of the codebase worked for my issue specifically, as I got more practice with reading tests or the files I didn't need as heavy reliance on AI.