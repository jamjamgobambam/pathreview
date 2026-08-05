# PathReview Contribution Journal

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/52

**Issue title:** Add a contribution_streak field to the GitHub analysis (longest consecutive days of commits)

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The current GitHub analysis does not show how consistently a user contributes over time. This issue adds a `contribution_streak` field that represents the longest sequence of consecutive days on which the user made commits. The main work will involve `agent/tools/github_tool.py` and understanding how the existing GitHub contribution data is retrieved and processed. A successful fix should calculate the streak correctly and include it in the existing GitHub analysis output.

**Selection notes:**
This issue has a clear expected result and identifies the main file involved. I will first inspect how the GitHub tool currently retrieves contribution activity and how its results are returned. The streak logic should involve collecting unique contribution dates, sorting them, and counting consecutive calendar days. The estimated four to six hour scope is realistic for the remaining project weeks.

**Branch name:** feat/52-contribution-streak

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/typicaleoxx/pathreview/commit/bbfd4aa928ce86d4e8f88bf1122ac300067c32f6

**Reproduction summary:**
I inspected `agent/tools/github_tool.py` and confirmed that the current tool only retrieves repository metadata. It does not retrieve contribution history, calculate consecutive commit days, or return a `contribution_streak` field.

**PLAN.md link:** https://github.com/typicaleoxx/pathreview/blob/feat/52-contribution-streak/PLAN.md


**Blockers or open questions:**
I still need to confirm whether the streak should use all user contributions or only commits from the repository provided in `repo_name`, and whether the project prefers GitHub GraphQL or REST API data.


## Week 9 - Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the contribution streak feature in `agent/tools/github_tool.py`. The tool now fetches user-wide commit contribution dates through GitHub GraphQL, removes duplicate dates, sorts them, and calculates the longest consecutive commit streak. I also added focused unit tests in `tests/unit/test_github_tool.py`.

**Next steps:**
I planned to finish the full validation, review the changes against the contribution guidelines, open the draft PR, and request feedback before marking it ready for review.

**Blockers:**
The repository already had unrelated unit test and Ruff failures, so I compared the baseline and final results to confirm that my changes did not introduce any new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/368

**Branch:** `feat/52-contribution-streak`

**What you built:**
I added a `contribution_streak` field to the GitHub analysis. It fetches the user’s commit contribution dates from the previous year, removes duplicate days, sorts them, and calculates the longest run of consecutive commit days.

**Tests added or updated:**
I updated `tests/unit/test_github_tool.py` with tests for empty histories, one-day activity, duplicate and unsorted dates, separate streaks, date boundaries, authentication, GraphQL errors, incomplete results, and the final metadata output. All 12 focused GitHubTool tests pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none
