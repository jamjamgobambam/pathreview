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