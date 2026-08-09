# Solution plan

**Issue:** [#52 Add a `contribution_streak` field to the GitHub analysis (longest consecutive days of commits)](https://github.com/ascherj/pathreview/issues/52)

## Understand

This is a feature gap, not a defect. Nothing in the codebase is broken, so there is no
faulty line to point at. The root cause is a missing capability:
`GitHubTool` (`agent/tools/github_tool.py`) is **repository-scoped and point-in-time**.
`_fetch_repo_metadata()` issues one REST call to `/repos/{user}/{repo}` and maps the
response onto ten keys. Every one of those keys describes what a repo looks like *right
now*: stars, forks, language, topics, open issue count, last push date. The tool has no
concept of a *user* acting *over time*, and it never queries any endpoint that returns
day-by-day activity.

**Expected:** `GitHubTool.execute()` returns a `contribution_streak` value alongside the
existing metadata, reporting the longest run of consecutive days the user contributed on.

**Actual:** The key does not exist. Verified by the reproduction test committed in
`5fa3296`:

```
$ .venv/bin/pytest tests/unit/test_github_tool.py -v -m unit
AssertionError: issue #52: GitHubTool returns no contribution_streak.
Got keys: ['description', 'fork_count', 'has_readme', 'homepage',
'last_commit_date', 'name', 'open_issues_count', 'primary_language',
'star_count', 'topics']
1 failed, 2 passed
```

Two control tests in that file pass. They pin the current ten-key output and prove the
mocked response is sound, so the single failure is a genuine missing field rather than a
broken fixture.

**Why the existing REST surface cannot answer this.** The daily contribution calendar is
not exposed over REST. `/users/{u}/events` is the closest REST option and it is capped at
roughly 90 days and 300 events, which would silently understate most streaks. The calendar
lives in GraphQL, under `user.contributionsCollection.contributionCalendar`. That is the
"second API surface" the Week 7 tier-2 assessment anticipated.

**Decision on what the streak measures.** The issue *title* says "consecutive days of
commits," but the *field name* is `contribution_streak`, and GitHub's calendar reports
combined daily contributions (commits, issues, PRs, reviews). This plan measures **total
daily contributions**, matching both the field name and the green-squares metric users
already recognize. Filtering to commits only would require walking
`commitContributionsByRepository` per repo per year, a much larger request budget for a
weaker match to the field name. This tradeoff is called out explicitly so a maintainer can
push back during PR review.

## Map

Files I expect to touch:

| File | Change |
| --- | --- |
| `agent/tools/github_tool.py` | Primary. Add `_fetch_contribution_streak()` and `_longest_streak()`, add a `graphql_url` attribute, add one key in `_fetch_repo_metadata()`. |
| `tests/unit/test_github_tool.py` | Already exists (reproduction). Extend with streak unit tests and mocked GraphQL fixtures. |

Files I have read and expect **not** to change:

- `agent/tools/base.py`. `ToolResult.data` is a plain `dict`, so a new key needs no
  interface change.
- `agent/orchestrator.py:94`. Calls `github_tool` with `github_username` and `repo_name`
  and stores `result.data` wholesale into `results[tool_name]`. A new key propagates for
  free.
- `api/schemas/*.py`. Checked all Pydantic models. None of them pin the tool's output
  shape, so an added key cannot fail validation.
- `rag/generator/prompt_templates.py`. Only interpolates `github_username`. Tool output
  does not currently reach the LLM prompt.

**Blast radius is small, which confirms the tier-2 sizing.** `grep -rn "Orchestrator("`
returns no instantiation anywhere in the repo, so the agent orchestrator is not yet wired
into the API request path. Adding this field cannot regress a live user flow. That also
means the field will not visibly change generated reviews until the orchestrator is wired
up, which is out of scope here and worth stating in the PR so nobody expects UI movement.

Functions involved:

- `GitHubTool.execute()`, entry point, needs no signature change.
- `GitHubTool._fetch_repo_metadata()`, builds the returned dict, gains one key.
- `GitHubTool._has_readme()`, the existing pattern for a token-optional secondary lookup
  that degrades quietly. The new fetch method should mirror its shape.

## Plan

1. **Add the GraphQL fetch.** New `_fetch_contribution_streak(username)`. POST to
   `https://api.github.com/graphql` with `Authorization: bearer {token}`. Query
   `user.createdAt` plus
   `contributionsCollection(from:, to:) { contributionCalendar { weeks { contributionDays { date contributionCount } } } }`.
   Return `None` immediately when `self.api_token` is unset, before any network call.

2. **Loop the history window.** `to` defaults to one year past `from`, so a single query
   cannot span a full account history. Walk backward in one-year windows from today to
   `user.createdAt`, collecting `(date, contributionCount)` pairs into one dict keyed by
   date. Keying by date deduplicates the padding days GraphQL returns at window edges,
   since the calendar is week-aligned and overlaps.

3. **Compute the streak.** New pure helper `_longest_streak(days: dict[str, int]) -> int`.
   Sort dates ascending, walk once, increment a counter when `contributionCount > 0` and
   the date is exactly one day after the previous counted date, reset to zero otherwise,
   track the max. Keeping this pure and separate from the network code is what makes it
   cheaply testable.

4. **Wire it in.** Add `"contribution_streak": self._fetch_contribution_streak(username)`
   to the metadata dict in `_fetch_repo_metadata()`. Wrap the call so a GraphQL failure
   degrades to `None` rather than failing the whole tool, matching how `_has_readme()`
   swallows its exceptions.

5. **Test it.** Flip the committed reproduction test green. Add table-driven cases for
   `_longest_streak()` covering empty input, all-zero days, a single day, a gap that
   breaks a run, and a streak crossing a year boundary. Mock `httpx.post` for the GraphQL
   path, reusing the `FakeResponse` helper already in the test file.

## Inputs & outputs

**Input.** Unchanged public interface: `execute({"github_username": str, "repo_name": str})`.
Internally the streak path uses only `github_username`, plus `self.api_token` from the
constructor. `repo_name` is irrelevant to it.

**Output.** The existing ten-key dict gains one key:

```python
{
    ...,                          # 10 existing keys, unchanged
    "contribution_streak": 47,    # int >= 0, or None when unavailable
}
```

`None` means "not measured" and is returned when no token is configured, when the GraphQL
call fails, or when the user does not exist. `0` means "measured, and the user has no
contributing days." Collapsing those two into `0` would be a lie, so they stay distinct.

**Side effects.** One extra HTTPS POST per year of account history, only when a token is
present. No writes, no persistence, no schema migration.

## Risks & unknowns

- **GraphQL requires authentication and the current tool does not.** Verified empirically:
  an unauthenticated POST to `api.github.com/graphql` returns `403`, while the REST call
  the tool already makes returns `200`. So this feature cannot preserve the tool's
  token-free behavior. Mitigation: return `None` when `self.api_token` is unset, so every
  existing field keeps working exactly as it does today. This is the single biggest
  constraint in the issue and the first thing to flag in the PR.

- **Request count scales with account age.** One query per year means a ten-year-old
  account costs ten requests on every `execute()` call. GraphQL bills by point cost
  against a 5000/hr budget. Mitigation: cap the lookback (five years is a reasonable
  default) and note the cap in the docstring. Unknown: whether maintainers would rather
  cache the value on the profile than recompute per call. Worth asking in the PR.

- **Private contributions are invisible without `read:user` scope.** A token missing that
  scope silently returns a lower streak rather than erroring, which is the worst failure
  mode because it looks like a correct answer. Mitigation: document the required scope in
  the method docstring and in the README's env var section.

- **`_fetch_repo_metadata()` becomes network-heavy.** It already makes two calls (repo,
  README). Adding N more makes a "fetch metadata" helper do substantially more work than
  its name suggests. Unknown: whether to keep it inline or expose the streak as a separate
  tool. Keeping it inline matches the issue text ("alongside the existing repo metadata")
  and the manifest, which scopes the change to `agent/tools/github_tool.py` only, so
  inline is the plan.

- **Pre-existing tooling friction.** The pre-commit mypy hook fails on
  `github_tool.py:135` (`warn_return_any`) independently of my change, and the file is not
  black-formatted, so any commit staging it triggers a ~40-line reformat. I deliberately
  left this alone in the reproduction commit. In Week 9 I will need to either fix the type
  error in the same PR or reformat separately. Reformatting risks conflicting with
  upstream, so my default is a one-line type fix and no reformat.

- **Streak semantics are timezone-dependent.** GitHub computes the calendar in the
  viewer's timezone, so the same account can show a different streak depending on who
  asks. Unknown, and low impact for a portfolio signal, but it means the number is not
  exactly reproducible across environments.

## Edge cases

The fix should handle each of these gracefully rather than raising:

- **No token configured.** Return `None`. Never issue the GraphQL request at all. This is
  the common local-dev path and must not break the other ten fields.
- **Streak spanning a year boundary.** A run from Dec 20 to Jan 10 must count as one
  22-day streak, not two. This is why step 2 merges all windows into a single date map
  before step 3 scans it, instead of computing a max per window.
- **Duplicate dates at window edges.** The calendar is week-aligned, so consecutive
  one-year windows overlap by a few days. Keying by date rather than appending to a list
  makes this a non-issue.
- **User with zero contributions.** Return `0`, distinct from `None`.
- **Brand-new account.** `createdAt` is inside the current window, so the backward loop
  must terminate immediately rather than querying a negative range.
- **Nonexistent or renamed username.** GraphQL returns `data.user: null` with a 200 status
  rather than an HTTP error, so a naive `response.raise_for_status()` will not catch it.
  Check for the null user explicitly and return `None`.
- **Today counted as a partial day.** A user mid-streak who has not committed yet today
  should not have the streak reset to zero. The scan counts only days with
  `contributionCount > 0`, and trailing zero days simply end the run without truncating
  the recorded max, so this falls out correctly.
- **Rate limited or 403 mid-loop.** Return `None` rather than a partial streak computed
  from the windows that happened to succeed. A partial answer here is worse than no
  answer.
