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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — not a feature this cohort (per Su26 note)

**Summary of feedback:**
No review came in — reviewer feedback isn't wired up for Summer 2026 per the course note. I did post PR #247 in Slack as a draft during Week 9 for informal peer input.

**How you responded:**
N/A — nothing to respond to.

---

### Reflection

**What was harder than you expected?**
Not the streak algorithm — that's a five-line sorted-list walk. What actually took time was the stuff around it: deciding what "correct" behavior even is when GitHub's API misbehaves. I only found the pagination problem because I tested against `torvalds/linux` and watched it try to walk 14,000+ pages — if I'd only tested against small repos I'd have shipped an unbounded loop. I also didn't expect to spend real time on process mechanics: `gh` wasn't installed, so I had to install and auth it mid-week, and it turned out I already had an open PR (#247) from Week 7 sitting there with stale placeholder content that I'd forgotten about, so "open a PR" actually meant "notice the old one and fix it" instead of starting clean.

**What did you learn about working in a large codebase?**
You inherit constraints you didn't choose. `GitHubTool` already had a `BaseTool`/`ToolResult` contract, an existing error-handling pattern in `execute()`, and a Conventional Commits + branch-naming convention — my job was to fit inside those, not redesign them. The bigger lesson was about the test suite itself: this repo has 54 pre-existing failing tests unrelated to my change, so "does `make test-unit` pass" isn't a yes/no question here — I had to diff my branch against a stashed baseline to prove I hadn't made anything worse, rather than just eyeballing green/red.

**How did AI tools help — and where did they fall short?**
AI was fastest at mechanical stuff: scaffolding the paginated-fetch loop, generating the `httpx` mock fixtures for 13 test cases, and catching lint issues (the `zip()` strict= warning, the `datetime.UTC` alias) I wouldn't have thought to check for. It fell short on the actual judgment calls — how far back to look, whether a page cap or a lookback window is the right bound, whether a failed commits call should fail the whole tool or degrade — those needed me to reason about the real GitHub API and this specific tool's contract, not just plausible-sounding code. I also had to double check that an AI-suggested detail (`httpx.Response.links` parsing the `Link` header) was real behavior and not a hallucinated convenience.

**What would you do differently if you started over?**
I'd check for an existing open PR on my branch before assuming I needed to open a new one — that cost me a confused round trip. I'd also wire `GITHUB_TOKEN` through properly from the start instead of leaving it unauthenticated; the streak feature adds up to 20 more API calls per profile on top of what was already there, and 60 requests/hour unauthenticated is not a lot of room.

**What are you most proud of from this module?**
The failure-degradation test (`test_commits_call_failure_degrades_to_zero_streak`). It's not flashy, but it's the one test that would have caught a real production bug — the naive version of this feature fails the entire tool the moment GitHub rate-limits you, silently losing star counts and README data that had nothing to do with the streak. Writing that test forced me to actually design for partial failure instead of assuming the happy path.
