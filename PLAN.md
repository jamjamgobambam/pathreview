## Solution plan

**Issue:** Add a `contribution_streak` field to the GitHub analysis (longest consecutive days of commits):
(https://github.com/ascherj/pathreview/issues/52)

### Understand
`GitHubTool` (agent/tools/github_tool.py) currently only reports static repo metadata (stars, forks, language, README presence, etc.) via `_fetch_repo_metadata`. There is no signal about a contributor's consistency over time. The stubbed method `_longest_contribution_streak` (line 140) already exists as a placeholder — it takes a `username`, has no body (`pass`), and isn't wired into `_fetch_repo_metadata` or the returned `metadata` dict. A correct implementation should pull the user's commit dates (via the GitHub REST commits endpoint or the GraphQL contributions calendar), reduce them to a sorted set of unique contribution days, and compute the longest run of consecutive calendar days. The result should show up as a new `contribution_streak` integer key in the dict returned by `execute()`.

### Map
- `agent/tools/github_tool.py` — `_longest_contribution_streak` (implement body), `_fetch_repo_metadata` (call it and add the key to `metadata`), `execute` (no change needed, just returns the dict)
- `agent/tools/base.py` — `ToolResult` — unchanged, just confirming the return shape the new field flows through
- `agent/orchestrator.py` (around line 94, `"github_tool"` invocation) — confirm no downstream code needs updating to surface the new field to callers/consumers
- `tests/unit/` — likely need a new `test_github_tool.py` (none currently exists based on the earlier grep) to cover the streak logic

### Plan
1. Decide and implement the data source: use `GET /repos/{username}/{repo_name}/commits?author={username}` (paginated) to collect commit timestamps, since the tool is already scoped to a single repo rather than global contributions.
2. In `_longest_contribution_streak`, convert each commit's `commit.author.date` to a `date` object, dedupe into a `set`, then sort and walk the sorted dates computing the longest run where each date is exactly one day after the previous.
3. Handle pagination (GitHub caps commit list responses at 30/page by default, 100 max) so a long streak isn't truncated to one page of results.
4. Wire the new method into `_fetch_repo_metadata`: call `self._longest_contribution_streak(username)` and add `"contribution_streak": streak_days` to the `metadata` dict (mirroring how `has_readme` is already computed via a helper and merged in).
5. Add error handling consistent with the rest of the file — reuse the same `httpx.HTTPStatusError` / `Exception` handling pattern as `_has_readme` (return 0 on failure rather than raising, since `_has_readme` already sets that precedent of "degrade gracefully, don't blow up the whole tool call").
6. Write unit tests (new `tests/unit/test_github_tool.py`) covering: no commits, one commit, an unbroken streak, and a streak with a gap.

### Inputs & outputs
- **Input:** `username` (str), plus implicitly `repo_name` since the commits endpoint is repo-scoped; reuses `self.api_token` and `self.base_url` already on the class.
- **Output:** an `int` representing the longest run of consecutive calendar days with at least one commit authored by `username` in that repo; `0` if the user has no commits or the repo/user doesn't exist.
- **Behavior change:** `_fetch_repo_metadata`'s returned dict gains a new key, `contribution_streak: int`, alongside the existing keys (`name`, `star_count`, etc.). This changes the shape of data that flows out of `GitHubTool.execute()` to whatever consumes it in `agent/orchestrator.py`.

### Risks & unknowns
- **Rate limiting:** the commits endpoint requires pagination for active repos/users, which multiplies GitHub API calls per analysis and increases the chance of hitting the same 403 rate-limit path already handled in `execute()` — need to confirm the existing 403 handling still applies when the failure originates inside `_longest_contribution_streak` rather than `_fetch_repo_metadata`.
- **Repo-scoped vs. account-wide streak:** the issue says "longest consecutive commit streak from their GitHub contribution history," which usually means the GitHub profile contribution graph (all repos, via GraphQL + auth token), not a single repo's commit log. Need to clarify with the issue author/maintainer whether repo-scoped (matches current tool's single-repo scope, REST-only, no extra auth) or account-wide (matches user intuition, requires GraphQL + a token with `read:user` scope) is expected — this materially changes the implementation.
- **Timezone/date boundary edge cases:** GitHub commit timestamps are UTC; a commit at 11:59pm and another at 12:01am UTC the next day could either correctly or incorrectly count as consecutive days depending on the contributor's actual timezone — unsure if this is worth normalizing to the user's local time or if UTC-day-boundary is acceptable.
- **Merge commits / bot commits:** unclear whether merge commits or commits authored by bots (e.g. dependabot) should count toward the streak; could inflate or deflate the result depending on repo conventions.

### Edge cases
- Username or repo has **zero commits** by that author — must return `0`, not raise or return `None`.
- Username/repo **doesn't exist** (404) — should degrade gracefully like `_has_readme` does, returning `0` rather than propagating the exception up through `execute()`.
- **Single commit** — streak should be `1`, not `0`.
- Commits made **on the same calendar day but at different times** (e.g. 5 commits in one day) — should count as one day, not artificially extend the streak.
- A **gap in the middle** of otherwise dense activity (e.g. commits on 10 consecutive days, then a 2-day gap, then 3 more consecutive days) — should return `10`, the longest run, not the total distinct days (13) or the most recent run (3).
- **Pagination boundary** — a streak that spans more commits than fit in a single API page must still be computed correctly, not silently truncated to the first page's commits.
