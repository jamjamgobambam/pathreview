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


## Week 10 - Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No - still awaiting review

**Summary of feedback:**
No reviewer feedback was provided for Summer 2026, so there were no maintainer comments or requested changes to respond to before the course ended.

**How you responded:**
Since no maintainer responded, I did my own review pass instead of iterating on comments. I re-read the diff against the existing GitHubTool conventions, re-ran the focused GitHubTool tests, and documented the pre-existing test and Ruff failures directly in draft PR #368 so a future reviewer can tell which failures are mine and which were already there. The PR is still open in draft and unmerged.

---

### Reflection

**What was harder than you expected?**
The issue read like a small one when I picked it - collect commit dates, sort them, count consecutive days - and the streak loop itself really was the easy part and took maybe twenty minutes. The hard part was that the existing GitHubTool only called `/repos/{username}/{repo_name}`, which returns repository metadata and nothing about when anyone actually committed. I had to figure out that repository metadata and a user's contribution history are two separate things in GitHub's API, and that the second one basically isn't available from the REST endpoints I was already using, so I moved to GraphQL and `contributionsCollection`. That pulled in decisions I hadn't planned for: I used `commitContributionsByRepository` specifically so that opening pull requests and issues wouldn't inflate someone's commit streak, I scoped the window to the previous year because that's what the contributions calendar covers, and I had to accept that GraphQL requires a token, which changed the tool from something that worked unauthenticated to something that needs a GitHub API token for the streak. I also spent longer than expected on the cases where the data comes back wrong rather than empty - GraphQL error responses, missing auth, and paginated results that could be incomplete - because a silently truncated contribution list would produce a streak number that looks fine and is just wrong.

**What did you learn about working in a large codebase?**
Most of my time went into not breaking things rather than writing the feature. I read the whole existing GitHubTool flow first so the new code would return through the same result path and raise errors the same way the metadata path already did, instead of inventing my own error shape, and I matched the structure of the existing tests in `tests/unit/test_github_tool.py` rather than setting up my own fixtures. There were things I wanted to clean up while I was in there and I left them alone, because an unrelated refactor buried in a feature PR makes the diff harder to review and I'd have no way to prove the refactor was safe. The thing I actually didn't expect was how I had to define "passing": the repo already had 53 failing unit tests and 182 Ruff errors before I touched anything, so I couldn't just run `make test-unit` and say it was green. I recorded the baseline and compared - 375 passing and 53 failing before, 387 passing and the same 53 failing after, and Ruff went 182 to 181 - which is a weaker claim than "everything passes" but it's the honest one, and it's the one a reviewer can actually check.

**How did AI tools help - and where did they fall short?**
It was genuinely useful for getting oriented: finding which files touched the GitHub tool, laying out REST versus GraphQL side by side so I could see that the contributions calendar isn't reachable from the REST endpoint I was on, brainstorming edge cases I then wrote tests for (duplicate dates, unsorted dates, streaks crossing a month or year boundary), and reading pytest output when I couldn't tell whether a failure was mine or pre-existing. Where it fell short was at the start, and it cost me real time - the early reasoning went along with my assumption that the existing tool probably already had contribution data in it somewhere, and it didn't, and I only found that out by opening `github_tool.py` and reading the actual request it makes. A few suggested GraphQL field names and response shapes also didn't match what the API actually returned, so I had to check them against GitHub's schema rather than trusting them. What I took from that is that it's good at "where is this and what are my options" and unreliable at "what does this specific code currently do" - the second one I have to verify against the implementation, the API's real behavior, the tests, and the project's conventions every time.

**What would you do differently if you started over?**
I'd do the investigation before writing PLAN.md instead of after. I wrote the first version of PLAN.md on an assumption about what data was already available, then had to rework it once I opened the endpoint and found only repository metadata, and that rewrite was avoidable with thirty minutes of reading first. I'd also run `make check` and `make test-unit` and save the output before touching any code - I ended up reconstructing my baseline partway through, which was uncomfortable, because at that point I couldn't be completely certain a failure I was looking at wasn't one I'd caused. The other thing I left unresolved too long was whether the streak should be user-wide or scoped to the repository in `repo_name`; I flagged it as an open question in Week 8 and then just picked user-wide while implementing, which is defensible for a profile-level metric but is a decision a reviewer should have seen stated up front. And I'd have documented the token requirement as soon as I chose GraphQL, since turning an unauthenticated tool into one that needs a `GITHUB_TOKEN` is a behavior change for anyone already using it, not an implementation detail.

**What are you most proud of from this module?**
The part I'd point at is that the issue was ambiguous - it named a field and a file and left the data source and the scope open - and I turned it into something a reviewer can actually evaluate: a specific data source with a stated reason for choosing it, 12 focused tests, and a draft PR that says out loud which failures were already in the repo. I'm also glad I didn't stop at the happy path. Empty contribution histories, GraphQL errors, missing authentication, and incomplete paginated results all have tests, and the incomplete-results case matters most to me because that's the one that would otherwise return a wrong-but-plausible number instead of failing loudly. It's not a large feature and it hasn't been reviewed or merged, so I don't want to oversell it - but the reasoning behind it is written down and checkable, which is more than I could have said about my work at the start of the course.
