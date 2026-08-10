## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/52

**Issue title:** Add a contribution_streak field to the GitHub analysis (longest consecutive days of commits)
 
**Tier:** Tier 2

**Problem summary:**
The current GitHub analysis reports information about a user's GitHub activity, but it does not measure contribution consistency over time. Because this metric is absent, users cannot easily demonstrate one aspect of sustained engagement with open-source projects. Consistent contribution activity is often viewed as a positive portfolio signal, so the analysis is missing information that could better represent a developer's coding habits.

A successful fix would add a new contribution_streak field to the GitHub analysis. This feature would calculate the longest sequence of consecutive days containing commits, and include that value in the analysis results so it can be displayed or used alongside the existing GitHub metrics.

I selected this issue because it is a well-scoped feature with a clear objective and a limited impact area. The work is on extending an existing feature by adding one additional tool that will display one additional metric rather than creating a new feature or redesigning an exisiting one. This fits in well with honing my skills of understanding existing code and integrating my code with the pre-existing test suite.

**Branch name:** (https://github.com/DanielGao2766/pathreview/tree/feat/52-contribution-streak-tool)

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/2152eb9c36d3de8cd5a43204a205afd6cf5b6838

**Reproduction summary:**
I located the gap in the feature within the agent/tools folder where I found github_tool.py. Since I could not find a method that calculates the longest commit streak of a user based on their github profile, I added a method stub that I will be implementing through the plan in the PLAN.md

**PLAN.md link:** (https://github.com/DanielGao2766/pathreview/blob/feat/52-contribution-streak-tool/PLAN.md)

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented `_longest_contribution_streak` in `agent/tools/github_tool.py` (replacing the stub from Week 8) and wired it into `_fetch_repo_metadata` as a new `contribution_streak` field. Switched the data source from the originally planned single-repo REST commits endpoint to GitHub's GraphQL `contributionsCollection` API, since account-wide streak (not repo-scoped) is the intended semantics per the issue. Added `tests/unit/test_github_tool.py` covering all edge cases from PLAN.md (no token, zero contributions, single day, unbroken streak, gap in the middle, same-day duplicate commits, nonexistent user, request failures, and integration into `_fetch_repo_metadata`).

**Next steps:**
Run `make check` and `make test-unit`, confirm no new failures vs. baseline, then open the PR and request review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/839)

**Branch:** feat/52-contribution-streak-tool

**What you built:**
Added a `contribution_streak` field to GitHub analysis output that reports the longest run of consecutive days with GitHub activity for a user's account, computed via GitHub's GraphQL `contributionsCollection` API. The field is now included in the dict returned by `GitHubTool.execute()` alongside existing repo metadata.

**Tests added or updated:**
Added `tests/unit/test_github_tool.py` (new file, 9 tests). Covers: no API token (bails out without a request), zero contributions, a single contribution day, an unbroken streak, a streak with a gap in the middle (verifies longest-run logic, not total days or most-recent run), multiple contributions on the same day collapsing to one day, a nonexistent user, an exception during the request, and that the field is correctly wired into `_fetch_repo_metadata`'s output.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** 
None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
The timeline of spending two weeks planning and then one week executing made me think that the workflow would be smooth since I already documented my decision choices in my PLAN.md, but some errors within my test file (test_github_tool.py) for isolated error cases that I thought of made me spend more time that I thought I would need on fixing the feature and left me with less time that I would have liked to create the test suite for the feature (longest_contribution_streak on GitHub)

**What did you learn about working in a large codebase?**
Something that was difficult that I had to learn while working in a large codebase was that I didn't know everything while making my own code, whereas for my own project I would know everything. This meant that when I ran the test suite through 'make check' and 'make test unit' within the test folder, some of the errors that didn't pass weren't part of my issue and I wasn't able to fix which is not typical my own self projects where every test has to pass and everything has to be green .

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI tools were most useful at the beginning by helping me figure out the codebase by helping me figure out what a specific method is supposed to do as an example and helping to review my PLAN.md whether to follow the GitHub API call that was already preexisting that would only pull stats from the repo I was contributing on or making a new request to pull from each individual's own GitHub profile for the last calendar year (365 days)

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I would create the test suite earlier so that the timeline would be better at the end of the project since after making my feature work in agent/tool/github_tool.py I still had to make tests since I was working on a new feature, and I didn't account for how long the test suite would take in both designing and fixing my code if the test failed in test_github_tool.py with tests like _calendar_response and _test_same_day_multiple_contributions_count_once. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I'm proud of developing my skills in being able to read and edit a large codebase, while being able to use AI effectively to help me finish my feature in a more efficient manner such as when it became a second set of eyes on my PLAN.md and helped come up with some potential errors within the code in github_tool.py so that I could put the tests in test_github_tool.py as unit tests for specific things that might cause errors such as having the GitHub user not be real that ended up with the test of test_nonexistent_user_returns_zero.
