## Solution plan

**Issue:** Add a `contribution_streak` field to the GitHub analysis (longest consecutive days of commits) — https://github.com/ascherj/pathreview/issues/52

### Understand
`GitHubTool._fetch_repo_metadata()` (`agent/tools/github_tool.py`) only calls
`GET /repos/{owner}/{repo}` for repo metadata and `HEAD /repos/{owner}/{repo}/readme`
to check for a README. Neither call touches commit history, so there is no code
path anywhere in the tool that could produce a streak value.

Expected behavior: the metadata dict returned by `execute()` includes a
`contribution_streak` integer — the longest run of consecutive calendar days on
which the given `github_username` made at least one commit to the given repo.

Actual behavior: confirmed via live reproduction against two real repos
(`octocat/Hello-World` and `sameeraagkan/Aura_`) — `execute()` returns
`['description', 'fork_count', 'has_readme', 'homepage', 'last_commit_date',
'name', 'open_issues_count', 'primary_language', 'star_count', 'topics']`,
with no `contribution_streak` key. Also confirmed in code: `last_commit_date`
comes from `pushed_at` on the repo-metadata response — a repo-level "last push"
timestamp, not per-commit data — so it can't be reused for a streak calculation.

### Map
- `agent/tools/github_tool.py` — main file to change:
  - Add a helper (e.g. `_fetch_commit_dates(username, repo_name)`) that calls
    `GET /repos/{owner}/{repo}/commits?author={username}`, paginated.
  - Add a pure helper (e.g. `_compute_contribution_streak(dates)`) that takes
    commit dates and returns the longest consecutive-day run.
  - Wire both into `_fetch_repo_metadata()` and add `contribution_streak` to
    the returned dict.
- `agent/tools/base.py` — no change; `ToolResult`/`BaseTool` contract already
  supports an arbitrary dict, no interface change needed.
- `agent/orchestrator.py` (~lines 89-100) — no change expected; it already
  passes `github_username` and `repo_name` into `github_tool`, which is all
  the new logic needs.
- `tests/unit/test_github_tool.py` — new file (created this week with one
  reproduction test); will grow to cover the real implementation.

### Plan
1. Add `_fetch_commit_dates()`: call `GET /repos/{username}/{repo}/commits`
   with `author={username}` and `per_page=100`, following the `Link` response
   header (`rel="next"`) to paginate, up to a capped number of pages.
2. Add `_compute_contribution_streak()`: parse each commit's
   `commit.author.date` (ISO 8601, UTC) into a `date`, dedupe same-day commits,
   sort, and walk the sorted list for the longest run of consecutive calendar
   days.
3. Wire the two together inside `_fetch_repo_metadata()` and add
   `"contribution_streak": streak` to the metadata dict.
4. Extend error handling: decide what `execute()` returns if the commits call
   fails (403 rate limit, 404, timeout) after the repo-metadata call already
   succeeded — likely default `contribution_streak` to `0` rather than failing
   the whole tool, since partial GitHub outages shouldn't take out README/star
   data too.
5. Write `tests/unit/test_github_tool.py` covering: correct streak for a known
   date list, 0 commits, 1 commit, non-consecutive commits, a streak spanning a
   pagination boundary, and the commits-call-fails path.

### Inputs & outputs
- Input: unchanged — `{"github_username": ..., "repo_name": ...}`, same as
  today. No new fields needed since commits are filtered by `author` within
  the already-provided repo.
- Output: existing metadata dict plus one new key,
  `"contribution_streak": <int>` (count of days).

### Risks & unknowns
- **Rate limits**: unauthenticated requests are capped at 60/hour (confirmed
  via `x-ratelimit-remaining` header during testing). Paginating commits for
  an active repo could burn through that fast on top of the two calls
  `_fetch_repo_metadata`/`_has_readme` already make. `GITHUB_TOKEN` (in
  `.env`) raises this limit but isn't wired into every call path yet — need to
  confirm `api_token` is actually passed through.
- **Unbounded pagination**: tested against `torvalds/linux`, which reported
  `rel="last"` at page 14639 — a truly unbounded loop would hang or blow the
  rate limit on a large/active repo. Need a hard cap (e.g. N pages or a
  lookback window like "last 12 months") rather than walking until `Link` has
  no `rel="next"`.
- **Author date vs. committer date**: each commit has both
  `commit.author.date` and `commit.committer.date`, which diverge on rebase/
  cherry-pick/squash. Need to deliberately pick author date (closer to "when
  the person actually worked") and document why.
- **Timezone/day boundary**: GitHub returns UTC timestamps (`...Z` suffix). A
  commit at 11:58pm vs 12:02am UTC splits one working session into two
  different calendar days. Normalizing to UTC calendar day is the simplest
  option and matches how GitHub's own contribution graph works, but it's
  worth being explicit about that choice.
- **Author filtering by email vs. login**: the `?author=` query param's exact
  matching behavior (GitHub login vs. commit author email) isn't fully
  verified — if a contributor's local git email isn't linked to their GitHub
  account, their commits could be undercounted.

### Edge cases
- Repo has 0 commits by the given author → `contribution_streak` should be
  `0`, not an error.
- Exactly 1 commit → streak of `1`.
- Multiple commits, all on the same calendar day → streak of `1`.
- Commits on adjacent calendar days (e.g. 11:59pm day 1, 12:01am day 2) →
  counted as 2 consecutive days.
- A gap of exactly one missed day between commits → streak resets there.
- Commit history spans more than one paginated page → streak must be computed
  over the full fetched set, not just page 1.
- Commits API call fails partway (rate limit, network error) after repo
  metadata already succeeded → tool should degrade gracefully rather than
  discarding the metadata it already has.
