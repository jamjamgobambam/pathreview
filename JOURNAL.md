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
