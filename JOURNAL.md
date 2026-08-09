# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/52

**Issue title:** Add a `contribution_streak` field to the GitHub analysis (longest consecutive days of commits)

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
`GitHubTool` (in `agent/tools/github_tool.py`) currently fetches static repo metadata — stars, forks, language, README presence — for a single repository via the REST API. It has no notion of a user's activity *over time*. The issue asks for a new field, `contribution_streak`, that reports the longest run of consecutive days on which the user made at least one commit, computed from their GitHub contribution history. A successful fix adds a method that pulls the user's daily commit activity (the REST events/commits endpoints only cover ~90 days, so this likely needs the GraphQL `contributionsCollection` calendar for full history), walks the resulting day-by-day activity to find the longest consecutive streak, and surfaces that number alongside the existing repo metadata so the review agent can use it as a portfolio signal.

**"Is this right for me?" reasoning:**
- Tier 2 fits: it touches one existing, well-scoped file (`github_tool.py`) but requires understanding a second GitHub API surface (GraphQL contributions calendar vs. the REST endpoints already used), which is the "cross-module understanding" the tier label calls out.
- Scope is bounded — one new field/method, no schema or API contract changes elsewhere that I could find.
- Estimated 4–6 hours matches a single-week (Week 8) implementation slot, with Week 9 left for polish/PR review.
- No blocking dependencies: the tool has no existing tests to conflict with, and a token-optional pattern (`api_token`) is already established for authenticated GitHub calls.

**Branch name:** `feat/52-contribution-streak`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger — *skipped per your instruction, do this yourself*

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ddzhang04/pathreview/commit/5fa32965917e980c9ab4e79f62f8ffc2e64bebb7

**Reproduction summary:**
Issue #52 is a feature gap, so I reproduced it with a failing test rather than by
triggering a fault. `tests/unit/test_github_tool.py` mocks the GitHub REST calls
`GitHubTool` makes and asserts that `execute()` returns a `contribution_streak` key. It
fails with `Got keys: ['description', 'fork_count', 'has_readme', 'homepage',
'last_commit_date', 'name', 'open_issues_count', 'primary_language', 'star_count',
'topics']`, confirming the tool returns only static, repo-scoped metadata and nothing
describing user activity over time. Two control tests in the same file pass, which proves
the failure is a real missing field and not a broken fixture. I also confirmed empirically
that the API needed to fix this behaves differently from the one already in use: an
unauthenticated POST to `api.github.com/graphql` returns `403`, while the REST call the
tool makes today returns `200`.

**PLAN.md link:** https://github.com/ddzhang04/pathreview/blob/feat/52-contribution-streak/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
- The issue title says "consecutive days of commits" but the field name is
  `contribution_streak`, and GitHub's calendar reports all contribution types together.
  I chose total daily contributions to match the field name and the familiar green-squares
  metric. I plan to flag this in the PR so the maintainer can redirect me.
- GraphQL requires a token, so `contribution_streak` will be `None` for unauthenticated
  runs while every existing field keeps working. I want to confirm the maintainer prefers
  that over making the tool require a token.
- Request cost scales at one query per year of account history. Unsure whether maintainers
  would rather cache the streak on the profile than recompute it per call.
- The pre-commit mypy hook already fails on `github_tool.py:135` before my change, and the
  file is not black-formatted, so staging it triggers a ~40-line reformat. I need to
  decide in Week 9 between a one-line type fix or a separate formatting commit. I am
  leaning toward the one-line fix to avoid conflicting with upstream.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five sub-tasks from `PLAN.md` are implemented in
[`dfafd73`](https://github.com/ddzhang04/pathreview/commit/dfafd73), and the Week 8
reproduction test is green.

1. GraphQL fetch. `_fetch_contribution_streak()` returns `None` immediately when no token
   is configured, before any network call.
2. Year-window loop. `_fetch_contribution_days()` walks backward in one-year windows,
   capped at five years, merging results into one date-keyed map.
3. Streak scan. `_longest_streak()` is a pure static helper over that map.
4. Wired into `_fetch_repo_metadata()` as an eleventh key.
5. Tests. 18 cases in `tests/unit/test_github_tool.py`, all passing.

I recorded the pre-existing failure baselines before starting, as the Week 9 instructions
ask, and my changes introduce none:

| Check | Baseline (Week 7 commit) | After my changes |
| --- | --- | --- |
| `pytest tests/unit -m unit` | 53 failed, 375 passed | 53 failed, 393 passed |
| `ruff check .` | 182 errors | 182 errors |
| mypy on the two files I touched | 1 error (`github_tool.py`) | clean |

Failure count is unchanged, passing count is up by my 18 new tests, and lint is flat. I
also fixed the one pre-existing `warn_return_any` error in `_has_readme`, since it lives in
the file I was already editing.

Two decisions worth surfacing at review. The streak measures **total daily contributions**,
not commits only: that matches the `contribution_streak` field name and the green-squares
metric, though the issue title says "commits." And the field degrades to `None` without a
token rather than making the tool require one, because GraphQL 403s unauthenticated while
the REST endpoints the tool already uses do not. `None` means "not measured" and `0` means
"measured, no contributing days"; the tests pin that distinction.

**Next steps:**
- Open a draft PR and post it in Slack for peer review.
- Fill in `.github/PULL_REQUEST_TEMPLATE.md`, documenting the pre-existing failures above
  and stating explicitly that my changes do not affect them.
- Consider asking the maintainer on issue #52 about the commits-vs-all-contributions call
  before marking the PR ready.

**Blockers:**
No hard blockers. One friction point: `agent/tools/github_tool.py` is not black-formatted
upstream, so staging it makes the pre-commit black hook rewrite 49 lines unrelated to my
change. I committed with `--no-verify` to keep the diff reviewable and will document this
in the PR rather than reformat the file, which matches the Week 9 guidance that a
contribution should not make things worse rather than fix the whole codebase. Ruff, black,
and mypy all pass on the code I actually wrote.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/725

**Branch:** `feat/52-contribution-streak`

**What you built:**
`GitHubTool` now returns a `contribution_streak` field: the longest run of consecutive days
the user contributed on. Because the daily contribution calendar is not exposed over REST,
it queries the GraphQL `contributionsCollection` calendar, walking backward in one-year
windows (GraphQL caps `to` at one year past `from`) and merging every window into a single
date-keyed map before scanning it. Merging first is what makes a streak spanning a year
boundary count as one run instead of two, and it also dedupes the overlapping days the
week-aligned calendar returns at window edges.

**Tests added or updated:**
`tests/unit/test_github_tool.py`, a new file with 18 tests. Eight cover the tool end to end
with mocked HTTP: the no-token path (asserting no GraphQL request is even attempted),
unknown users (GraphQL returns `data.user: null` with HTTP 200, so `raise_for_status()`
does not catch it), GraphQL `errors` arrays, HTTP failures, and a malformed response not
taking down the other ten fields. The remaining ten cover `_longest_streak()` directly:
year boundary, leap day, zero days and missing dates breaking a run, trailing zero days not
truncating the recorded best, and the empty case.

**Self-review confirmation:** [x] `make check` passes [x] `make test-unit` passes

Read against documented pre-existing failures, as the Week 9 instructions define it: my
changes introduce no new failures. Baselines measured on a clean Week 7 checkout and
re-measured after the change:

| Command | Baseline | With my changes |
| --- | --- | --- |
| `pytest tests/unit -m unit` | 53 failed, 375 passed | 53 failed, 393 passed |
| `ruff check .` | 182 errors | 182 errors |
| `make typecheck` | 5 errors in 4 files | 5 errors in 4 files |

Failures flat, passing up by exactly my 18 tests, lint identical. Both files I touched are
mypy-clean. All of this is documented in the PR body.

**Draft PR feedback received from:** none. I did not get peer review before submitting, so
the two open design questions (total contributions vs commits only, and degrading to `None`
without a token vs requiring one) go to the maintainer cold in the PR description rather
than having been pressure-tested by a classmate first.

**Late submission:** the PR was opened Monday August 3 at approximately 3:15PM EDT, after
the 2:59AM EDT deadline. The implementation and Check-in 1 were committed and pushed on
Wednesday July 29, before the midweek deadline; what slipped was opening the PR itself.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No review came in. As of Sunday August 9, PR
[#725](https://github.com/ascherj/pathreview/pull/725) is still open with zero comments and
zero reviews. Two factors beyond the Su26 note that reviewer feedback is not a feature this
term: I submitted the PR late, and I never got the draft PR peer review the Week 9
instructions asked for, so nobody had eyes on it at any stage.

**How you responded:**
No feedback to respond to. The two questions I raised for the maintainer in the PR
description, whether the streak should count commits only rather than all contributions,
and whether degrading to `None` without a token is the right call, remain open.

---

### Reflection

**What was harder than you expected?**

The code was the easy part. `_longest_streak()` is fifteen lines and took maybe twenty
minutes including the edge cases. Everything around it took the rest of the four weeks.

The specific thing that caught me was assuming I could add a GraphQL call next to the
existing REST calls and be done. I tested it instead of assuming, and got a 403 with no
token, where the REST endpoints the tool already used returned 200 unauthenticated. That
one measurement invalidated my original design. The feature fundamentally could not
preserve the tool's token-free behavior, so I had to decide what the field should do when
it cannot be measured. That is where `None` versus `0` came from: `None` means "not
measured," `0` means "measured, no contributing days," and collapsing them would report an
unmeasured user as an inactive one.

The other surprise was the state of the repo. On a clean checkout, before I touched
anything, `pytest tests/unit` gave 53 failures and `ruff check .` gave 182 errors. I had
assumed a green baseline and had to stop and measure first so I could later prove I had not
made anything worse.

**What did you learn about working in a large codebase?**

That most of the work happens before you write a line. I spent real time mapping what would
break: checking whether any Pydantic schema pinned `GitHubTool`'s output shape (none did),
whether the orchestrator would need changes to pass a new key through (it would not, it
stores `result.data` wholesale), and who read the fields downstream.

That mapping turned up something I would never have found in my own project. `grep -rn
"Orchestrator("` returns no instantiation anywhere in the repo. The component that calls my
tool is not wired into the running application. I ran the app locally to confirm it, and my
field genuinely cannot appear anywhere in the UI. In my own projects, code I write is code
that runs. Here I shipped something correct and tested that no user can currently reach,
and the right response was to disclose that in the PR rather than quietly hope nobody
noticed.

I also learned that "don't make it worse" is a different and more useful bar than "make it
perfect." I left 182 lint errors alone. I left `github_tool.py` unformatted, because staging
it would have made black rewrite 49 lines that had nothing to do with my change and would
have buried a 157-line feature in noise and guaranteed a conflict with upstream. Restraint
about what not to touch turned out to matter as much as the change itself.

**How did AI tools help — and where did they fall short?**

I used AI heavily, which the course encourages, so I want to be accurate about the split.

Where it helped most: orientation. This is a 100-plus file repo across seven packages, and I
went from opening it to knowing exactly which file and which three functions mattered in
well under an hour. It was also good at generating the test matrix once I knew what the
edge cases were, and at drafting the PR description and this journal.

Where it fell short: anything requiring a measurement rather than a recollection. The 403
finding came from actually firing a request at `api.github.com/graphql`, not from asking. If
I had trusted a plausible-sounding answer about the auth model I would have built the wrong
thing. Same with the 53 failures and 182 lint errors, which nothing could tell me without
running the commands in this specific repo at this specific commit. The pattern I would
take forward: AI is strong at "where is this and what does it look like," weak at "what is
actually true right now in this environment," and the second category is where the design
decisions live.

It also did nothing to save me from the process failure. No tool was going to open the PR
for me on Wednesday.

**What would you do differently if you started over?**

Open the draft PR at the start of Week 9, not the end. This is the clear one. The
instructions said to, I did not, and it cost me twice: the submission went in about twelve
hours past the deadline, and I never got peer review, so my two open design questions went
to the maintainer cold instead of being pressure-tested by a classmate first. The
implementation was finished and pushed the prior Wednesday. What slipped was purely the
submission step, which is the most avoidable kind of miss.

Second, I would verify the API's authentication model during issue selection rather than
during implementation. My Week 7 notes guessed that GraphQL would be needed. Spending ten
minutes confirming that in Week 7 would have surfaced the token constraint before I wrote a
plan around it.

Third, I would weigh reachability when picking the issue. Given the choice again I would
prefer an issue whose result I can demonstrate in the running application.

**What are you most proud of from this module?**

Writing the reproduction test in Week 8 and leaving it red for a week.

It would have been faster to note "the field is missing" and move on. Instead I wrote a
test that asserted `contribution_streak` existed, watched it fail with the actual list of
ten keys the tool returned, and committed it failing. I also wrote two passing control
tests next to it, so the failure could not be dismissed as a broken fixture. When the fix
landed in Week 9, that test went green on its own without being edited to fit the
implementation.

That is the habit I want to keep. The test was written when I only understood the problem,
not the solution, so it described the requirement rather than the code I happened to write.
