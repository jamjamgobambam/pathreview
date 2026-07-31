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