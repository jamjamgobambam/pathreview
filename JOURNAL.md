# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/52

**Issue title:** Add a `contribution_streak` field to the GitHub analysis (longest consecutive days of commits)

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The agent's GitHub analysis tool (`agent/tools/github_tool.py`) currently reports on a
user's repositories and activity, but has no way to measure how consistently someone
contributes over time. Right now the tool can't distinguish a developer with steady,
sustained activity from one with a single burst of commits, even though consistency is a
meaningful signal for a portfolio reviewer. A successful fix adds a `contribution_streak`
field that computes the longest run of consecutive days with at least one commit from the
user's GitHub contribution history, and wires that value into the tool's output alongside
the other GitHub analysis fields.

**Scope reasoning ("Is this right for me?"):**
This is labeled Tier 2 ("intermediate — requires cross-module understanding"), not Tier 1,
so I went in with eyes open that it touches more than an isolated bug fix. It's scoped to a
single file (`agent/tools/github_tool.py`) with a clear, well-defined feature request and no
ambiguity about what "done" looks like, which keeps it tractable. The main added work
versus a Tier 1 issue is that no test file is pre-listed, so I'll need to understand the
existing `BaseTool` interface and the agent orchestration wiring well enough to write my own
unit tests, per `docs/CONTRIBUTING.md`. Estimated effort is 4–6 hours, which fits the
Module 3 timeline.

**Branch name:** `feat/52-contribution-streak`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SameeraaGKan/pathreview/commit/f8e1692

**Reproduction summary:**
Ran `GitHubTool.execute({"github_username": ..., "repo_name": ...})` directly
against two real repos (`octocat/Hello-World` and my own `sameeraagkan/Aura_`)
and inspected the returned data keys — no `contribution_streak` field, and no
commit-history fetch anywhere in `github_tool.py`. Also confirmed `GET
/repos/{owner}/{repo}/commits` returns each commit's date nested at
`commit.author.date`, and that pagination works via the `Link` response
header. Committed a failing unit test
(`tests/unit/test_github_tool.py::test_contribution_streak_field_missing`)
that asserts `"contribution_streak" in result.data` — it fails today (red),
which documents the gap in a way that will flip to passing once the fix
lands.

**PLAN.md link:** https://github.com/SameeraaGKan/pathreview/blob/feat/52-contribution-streak/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Haven't confirmed exactly how GitHub's `?author=` filter matches (GitHub
login vs. commit email) or how to keep pagination bounded on a very active
repo without an arbitrary cap. Also need to decide whether `GITHUB_TOKEN`
should be required (vs. optional) for this feature given the 60/hour
unauthenticated rate limit.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are implemented. Added `_fetch_commit_dates()`
(paginated `GET /repos/{owner}/{repo}/commits?author=...`, bounded to the
last 365 days via `since` and capped at 20 pages as a backstop) and
`_compute_contribution_streak()` (pure function, dedupes same-day commits
and walks sorted dates for the longest consecutive run) in
`agent/tools/github_tool.py`. Wired both into `_fetch_repo_metadata()`,
adding `contribution_streak` to the returned dict. Resolved the two open
questions from Week 8: used author date (not committer date, documented
in the docstring) and made the commits fetch degrade to a streak of `0`
on any failure (rate limit, 404, malformed response) rather than failing
the whole tool, so a GitHub hiccup doesn't discard the repo metadata that
already succeeded. Rewrote `tests/unit/test_github_tool.py` — the
original reproduction test now passes and acts as a regression guard,
plus 10 new tests covering: 0 commits, 1 commit, non-consecutive commits,
same-day dedup, a streak spanning a pagination boundary, the
commits-call-fails path, and direct unit tests of the pure streak
calculation (empty list, unsorted input, multiple runs).

**Next steps:**
Push the branch, open a draft PR, and request review in the course Slack
channel before marking it ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/247 (currently draft — pending peer/mentor review before marking ready)

**Branch:** `feat/52-contribution-streak`

**What you built:**
Added a `contribution_streak` field to `GitHubTool`'s output: the longest
run of consecutive calendar days on which the given GitHub user made at
least one commit to the given repo, computed from paginated commit
history filtered by author and bounded to the last 12 months.

**Tests added or updated:**
`tests/unit/test_github_tool.py` — 13 tests total covering the full
tool (`execute()` with mocked `httpx`) and the pure streak-computation
helper directly: field presence, zero/one/multiple commits, gaps,
same-day dedup, pagination boundaries, and graceful degradation when the
commits API call fails.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(53 pre-existing failures unrelated to this change remain — same count
as the documented baseline minus the one github_tool test this fix now
makes pass; no new failures introduced, confirmed by diffing against a
`git stash` baseline run. `ruff check .` reports the same 181
pre-existing errors before and after this change.)

**Draft PR feedback received from:** [pending]
