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