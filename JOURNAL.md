## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/52

**Issue title:** Add a contribution_streak field to the GitHub analysis (longest consecutive days of commits)

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

I am already familiar with contributing to large codebases, so I am comfortable working with issues that require an understanding of how modules connect. The issue I selected has a relatively focused scope and the surrounding code is straightforward enough for me to understand it even with a brief initial overview.

**Problem summary:**
The `GitHubTool` currently pulls a static snapshot of repository metadata, but it never inspects commit history, so a reviewer gets no signal about how consistently the author actually works on a project. This issue asks for a new `contribution_streak` field that reports the longest run of consecutive calendar days on which the repo received at least one commit. The tool currently only calls the `/repos/{owner}/{repo}` endpoint and reads `pushed_at`, which reflects the most recent activity but says nothing about sustained cadence. A successful fix would fetch the repo's commit history (via the paginated `/repos/{owner}/{repo}/commits` endpoint), bucket commits by day, compute the longest consecutive-day streak, and add it to the metadata dict returned by `_fetch_repo_metadata`. All of this lives in `agent/tools/github_tool.py`, next to the existing metadata extraction.

**Branch name:** feat/52-github-contribution-streak

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/tifflia/pathreview/commit/98107e61bcd014b4e804908377dfaeab15221608

**Reproduction summary:**
I called `GitHubTool.execute()` against a real public repo and inspected the returned metadata: the call succeeds but the dict has no `contribution_streak` key, confirming the gap lives in `_fetch_repo_metadata()` in `agent/tools/github_tool.py`, which only queries `/repos/{owner}/{repo}` and never the `/commits` endpoint. I captured this as an `xfail(strict=True)` reproduction test in `tests/unit/test_github_tool.py`.

**PLAN.md link:** https://github.com/tifflia/pathreview/blob/feat/52-github-contribution-streak/JOURNAL.md

**Blockers or open questions:**
While creating my reproduction test, I noticed that when I tried to follow the format of other unit tests the linter failed and mypy caught some type errors. I wonder if that was supposed to happen and whether that means all of the other unit tests are not up to date in formatting and need to be fixed.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've implemented the actual functions in `agent/tools/github_tool.py`. I added the two new helpers from PLAN.md `_longest_streak(commit_days)`and `_fetch_commit_dates(username, repo_name)`. I then wired these into `_fetch_repo_metadata()` so the returned metadata dict now includes the `contribution_streak` key, with a graceful fallback to 0 if the commits request fails so the rest of the snapshot still comes back.

**Next steps:**
Writing the unit tests. I'll flip the existing xfail reproduction test into a passing assertion and add coverage for `_longest_streak` (empty, single day, gaps, out-of-order input) and for the paginated `/commits` fetch, following the mock-based patterns already in `tests/unit/test_github_tool.py`.

**Blockers:** No blockers as of yet.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/434

**Branch:** feat/52-github-contribution-streak

**What you built:**
I added a `contribution_streak` field to the GitHub metadata that reports the longest run of consecutive calendar days on which the repo received at least one commit. `GitHubTool` now pages through the `/repos/{owner}/{repo}/commits` endpoint (following the `Link` header's `next` relation), buckets each commit's author timestamp into a UTC calendar day, and computes the longest unbroken day-over-day run via a pure `_longest_streak` helper. If the commits request fails it degrades to `0` so the rest of the metadata snapshot still returns successfully.

**Tests added or updated:**
All in `tests/unit/test_github_tool.py`. I flipped the existing issue-#52 reproduction test from `xfail` into a passing regression assertion, added unit tests for `_longest_streak` (empty set, single day, gaps, out-of-order input, month-boundary crossing), and added tests for `_fetch_commit_dates` covering `Link`-header pagination across two pages and graceful degradation to `[]` on error, plus an `execute()`-level test proving a failing `/commits` request still returns the other metadata with `contribution_streak == 0`.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

Neither whole-repo command passes on my branch, but the failures are pre-existing and unrelated to my change: `make check` fails at the lint step with 181 errors in files I never touched (e.g. `test_tech_detector.py`), and `make test-unit` has 53 failures in other modules that reproduce identically on a clean checkout. My changed files are clean on all checks individually — `ruff check` and `mypy` pass on `agent/tools/github_tool.py`, and all 10 tests in `tests/unit/test_github_tool.py` pass.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was reproducing the issue, which I had assumed would be the easy step. `GitHubTool` is only one of several tools in the review pipeline — the orchestrator builds an execution plan and runs it alongside `tech_detector`, `readme_scorer`, and the others, and only when the profile happens to include a `github_username` plus a project with a `github_repo`. Running the pipeline end to end gave me one big nested `tool_results` blob, and a missing field inside it doesn't show up as a failure: nothing errors, the review just comes back with less information than it should have. So before I could demonstrate anything I had to work out how to single the tool out from the rest of the pipeline, calling `GitHubTool.execute()` on its own against a real public repo and inspecting the returned metadata dict directly. Only then could I show the gap concretely — the call succeeds, but there is no `contribution_streak` key — and pin it to `_fetch_repo_metadata()` never touching the `/commits` endpoint. Reproducing a *missing feature* turned out to be a different skill from reproducing a bug, since I had to construct the narrowest place where an absence becomes observable rather than just triggering something that breaks.

The other thing that caught me off guard came when I wrote the tests for the code I generated. I deliberately followed the format and approach used by all the other unit tests in `tests/unit/test_github_tool.py`, assuming that matching the existing conventions was the safe choice, and ruff and mypy still flagged errors in what I'd written. I was confused about how my tests could fail the checks when every pre-existing test around them was written the same way. Once I dug in, the answer was that those tests predate the current lint and type-check configuration and were never brought up to date, so "consistent with the codebase" and "passes the codebase's own checks" were two different targets. That meant I couldn't use the surrounding code as a style reference the way I expected to, and I had to decide for myself which standard to write to.

**What did you learn about working in a large codebase?**
When writing code, especially when it comes to writing tests, I learned the importance of thinking about callers I can't see. In my own projects, if something fails I can just raise and fix it, because I'm the only consumer. Here I had to decide what `_fetch_repo_metadata()` should return when the `/commits` request fails, and I chose to degrade `contribution_streak` to `0` so the rest of the metadata snapshot still comes back rather than failing the whole tool call. That keeps existing consumers of the tool working, but it also means `0` is ambiguous: downstream code can't distinguish "this author commits inconsistently" from "GitHub rate-limited us." That kind of tradeoff barely exists when you own every call site, and it's the sort of thing I now know to name explicitly in a PR description instead of quietly picking one.

**How did AI tools help — and where did they fall short?**
AI was most useful for mechanical work with a clear pattern to follow: scaffolding the mock-based HTTP tests to match the existing style in `tests/unit/test_github_tool.py`, getting the `Link`-header pagination loop right, and clearing ruff and mypy complaints. It was also good at enumerating edge cases for `_longest_streak` — empty input, a single day, gaps, out-of-order dates, crossing a month boundary — which turned into most of my test coverage.

Where it fell short was environment and setup debugging. Getting the app running locally, I hit problems with my Docker setup while running the `make` targets, and AI had a hard time isolating what was actually wrong. Because the failure surfaced several layers away from its real cause, it kept proposing plausible-sounding fixes based on the error text — generic Docker troubleshooting, tweaking commands, reinstalling things — without ever narrowing down which part of this project's setup I had gotten wrong. Some of those suggestions would have changed my environment for no reason, so I stopped following them. What actually resolved it was sitting down and reading the project's own documentation, `docs/SETUP.md` and `docker-compose.yml`, which made clear what services the stack expects and what state they need to be in before the `make` targets will work. Once I understood the intended setup, my mistake was obvious in a way it never was from the error output alone. The lesson I took from that is that AI is strong when the problem is contained in code it can see, and much weaker when the problem lives in my machine's state — and that reading the maintainers' docs first would have been faster than debugging by suggestion.

**What would you do differently if you started over?**
First, I'd bound the commit fetch from the start. `_fetch_commit_dates` follows the `next` link until there are no pages left, so a repository with several thousand commits costs dozens of API calls for a single analysis, against an unauthenticated rate limit of 60 requests per hour. Capping it to a fixed number of pages or a recent time window, and documenting that the streak is computed over that window, would have been the better first version. I'd also capture the clean-`main` baseline in Week 8 rather than rediscovering it during Week 9 self-review, and I'd keep the formatter churn in its own commit so the feature commit reads cleanly.

**What are you most proud of from this module?**
How I drew the line between the logic and the I/O, and the test coverage that decision bought me. It would have been faster in the moment to compute the streak inline inside `_fetch_repo_metadata()`, but I pulled it out into `_longest_streak`, a pure static helper that takes a set of dates and returns an integer and does no network work at all. That one boundary is what made the rest of the testing straightforward: I could exercise the real logic with plain data instead of building elaborate HTTP mocks around it.