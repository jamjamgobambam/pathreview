## Solution plan

**Issue:** [#52 - Add a contribution_streak field to the GitHub analysis (longest consecutive days of commits)](https://github.com/ascherj/pathreview/issues/52)

### Understand

The specific gap I'm fixing: **`GitHubTool` reports a static repo snapshot but no signal about commit cadence.** Right now the tool fetches repository metadata and reads `pushed_at` (which only tells you *when the repo was last touched*), but it never looks at commit history, so a reviewer can't tell whether the author committed steadily over many days or dumped everything in one sitting.

I need to add a new `contribution_streak` field to the metadata: an integer equal to the **longest run of consecutive calendar days on which the repo received at least one commit**. A correct implementation fetches the repo's commit history, groups commits by the calendar day they were authored, and computes the longest unbroken day-over-day streak.

- **Expected:** metadata dict contains `"contribution_streak": <int>`, e.g. commits on Jan 13, 14, 15 then a gap then Jan 18 → streak of `3`.
- **Actual (reproduced):** the metadata dict has no `contribution_streak` key at all. Confirmed via a live call and captured as an `xfail(strict=True)` reproduction test — see the Reproduction section below.

### Map

Files / functions I expect to touch:

- **`agent/tools/github_tool.py`** — the core change.
  - `_fetch_repo_metadata()` (builds the metadata dict) — add `"contribution_streak"` to the returned dict.
  - New helper `_fetch_commit_dates(username, repo_name)` — call the paginated `/repos/{owner}/{repo}/commits` endpoint, following `response.links["next"]` until there are no more pages, and collect each commit's authored date.
  - New pure helper `_longest_streak(commit_days)` — take the set of commit calendar days and return the longest consecutive-day run. Kept separate so it's unit-testable without hitting the network.
- **`tests/unit/test_github_tool.py`** — flip the existing reproduction test from `xfail` to a passing test, and add unit tests for `_longest_streak` (empty, single day, gaps, out-of-order pages) plus a paginated-`/commits` mock.

Files I need to be *aware of* but likely won't change (they consume the dict by key and will pass the new field through transparently):

- `agent/orchestrator.py` (~line 122) threads `repo_metadata` to downstream tools.
- `ingestion/pipeline.py` `ingest_repo_metadata()` serializes the dict for storage.

### Plan

1. **Add `_longest_streak(commit_days: set[date]) -> int`** — pure function. Sort the unique days; walk them tracking the current run, resetting when the gap between consecutive days is more than one day; return the max run. Return `0` for an empty set.
2. **Add `_fetch_commit_dates(username, repo_name) -> list[date]`** — GET `/repos/{username}/{repo_name}/commits?per_page=100`, reuse the existing auth header logic, and paginate by following the `next` link header. Parse each commit's `commit.author.date` (ISO-8601) into a `date`.
3. **Wire it into `_fetch_repo_metadata()`** — call the two helpers and add `"contribution_streak": self._longest_streak(set(commit_dates))` to the metadata dict, alongside the existing keys.
4. **Handle failures gracefully** — if the commits request fails or the repo is empty, default `contribution_streak` to `0` rather than letting the whole `execute()` call fail (the snapshot fields should still come back).
5. **Update tests** — remove the `xfail` marker from `test_repro_issue_52_metadata_includes_contribution_streak` so it becomes a real passing assertion, and add the `_longest_streak` / pagination unit tests above.

### Inputs & outputs

- **Inputs (unchanged public interface):** `GitHubTool.execute()` still takes `{"github_username": str, "repo_name": str}`. Internally the new work also consumes the JSON from `/repos/{owner}/{repo}/commits` — a list of commit objects where I read `commit.author.date`.
- **Outputs (what changes):** the `dict` returned by `_fetch_repo_metadata()` (and therefore `ToolResult.data`) gains one key, `contribution_streak: int`. No existing keys change type or meaning. New private helpers `_fetch_commit_dates` and `_longest_streak` are added; no signature of an existing method changes.
- **Behavioral change:** the tool now makes **additional** HTTP calls (one per page of commit history) beyond the current single `/repos/...` + `/readme` calls.

### Risks & unknowns

- **Rate limiting (`agent/tools/github_tool.py`, the new `/commits` calls):** unauthenticated requests are capped at 60/hour, and paginating history multiplies request count. Risk that a large repo exhausts the budget or returns 403. Need to decide how many pages to fetch and reuse the existing 403 handling in `execute()`.
- **Timezone / date bucketing (`_longest_streak`):** commit timestamps are timezone-aware ISO-8601; "consecutive calendar days" is ambiguous across timezones. Unknown whether to bucket in UTC or the commit's local offset — I'll standardize on UTC dates and document it.
- **Author vs committer date (`_fetch_commit_dates`):** `commit.author.date` and `commit.committer.date` can differ (rebases, cherry-picks). Need to pick one deliberately; I plan to use author date and note the choice.
- **Pagination mechanics (`_fetch_commit_dates`):** relying on the `Link` header's `next` relation; unknown exactly how `httpx` surfaces it (`response.links`) — needs verification against a real paginated response.

### Edge cases

The fix must handle these gracefully:

1. **Repo with zero commits** (brand-new/empty repo, or the `/commits` endpoint returns `[]` / a 409 "Git Repository is empty") → `contribution_streak == 0`, and `execute()` still returns the other metadata successfully.
2. **All commits on a single day** (e.g. a weekend hackathon project) → `contribution_streak == 1`, not the total commit count.
3. **Non-chronological / paginated ordering** — GitHub returns commits newest-first and split across pages; the streak calc must not assume sorted input, so I bucket into a set of days before computing.
4. **Multiple commits on the same day** count as one day toward the streak (dedupe by calendar day, not by commit).
5. **Commits request fails while the repo lookup succeeds** (rate limit / transient error on `/commits` only) → degrade to `contribution_streak == 0` instead of failing the whole tool call.