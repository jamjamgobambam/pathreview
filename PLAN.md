## Solution plan

**Issue:** Add a `contribution_streak` field to the GitHub analysis (longest consecutive days of commits) - https://github.com/ascherj/pathreview/issues/52

### Understand

**Expected behavior:** When `GitHubTool.execute()` runs for a valid `github_username` and `repo_name`, the returned metadata dict should include a `contribution_streak` integer representing the user's longest run of consecutive calendar days with at least one commit in that repository's history

**Actual behavior:** `_fetch_repo_metadata()` in `agent/tools/github_tool.py` only returns static repo fields (name, description, star_count, last_commit_date). There is no API call to fetch commit history and no streak calculation. The orchestrator in `agent/orchestrator.py` passes tool results downstream unchanged, so nothing in the analysis pipeline currently exposes contribution consistency

**Root cause:** The feature was never implemented. `GitHubTool` fetches a single `/repos/{owner}/{repo}` response and stops. Streak computation requires an additional data source (commit dates) and a helper to find the longest consecutive-day run.

### Map

Files/modules involved:

| File | Role |
|---|---|
| `agent/tools/github_tool.py` | **Primary change.** Add commit-history fetch, streak calculation, and include `contribution_streak` in the metadata dict returned by `_fetch_repo_metadata()` or `execute()`. |
| `tests/unit/test_github_tool.py` | Add/update unit tests: reproduction test becomes passing; add streak-calculation tests with mocked commit dates. |
| `agent/orchestrator.py` | **Read-only for now.** Confirms `github_tool` is invoked with `github_username` + `repo_name`; no change expected unless we need to pass extra params. |
| `core/config.py` | **Optional read.** `github_token` may be needed to avoid rate limits when paginating commits. |

Functions I expect to add or modify in `github_tool.py`:
- `_fetch_repo_metadata()` - add `contribution_streak` to returned dict
- `_fetch_commit_dates()` (new) - paginate GitHub commits API for the repo
- `_calculate_longest_streak()` (new) - pure function: list of dates → longest consecutive-day count

### Plan

1. **Add a commit-history fetch helper in `github_tool.py`.** Create `_fetch_commit_dates(username, repo_name)` that calls `GET /repos/{username}/{repo_name}/commits` (with auth header if `self.api_token` is set), paginates until enough history is collected or pages run out, and extracts the commit date (use `commit.author.date` or `commit.committer.date`) normalized to UTC calendar dates

2. **Implement streak calculation as a pure helper.** Create `_calculate_longest_streak(dates: list[date]) -> int` that deduplicates dates, sorts them, scans for the longest run where each day is exactly one calendar day after the previous, and returns the count (return `0` for empty input, `1` for a single day)

3. **Wire streak into tool output.** In `_fetch_repo_metadata()`, call the helpers and set `"contribution_streak": streak` in the metadata dict alongside existing fields like `star_count` and `last_commit_date`

4. **Handle API failures gracefully.** If commit fetch fails (403 rate limit, empty repo, network error), log the error and set `contribution_streak` to `0` rather than failing the entire tool - repo metadata should still return successfully

5. **Write unit tests in `tests/unit/test_github_tool.py`.** Convert the reproduction test into a passing test; add cases for a known streak pattern, a single-day streak, no commits, and API error fallback all using mocked `httpx` responses so tests don't hit the real GitHub API.

### Inputs & outputs

**Inputs (unchanged):**
- `execute(input_data)` expects `{"github_username": str, "repo_name": str}`
- Optional `GitHubTool(api_token=...)` from `core/config.py` settings for authenticated requests

**Outputs (changed):**
- On success, `ToolResult.data` metadata dict gains:
  - `"contribution_streak": int` - longest consecutive days with ≥1 commit in this repo
- Existing fields (`name`, `star_count`, `last_commit_date`, etc.) remain unchanged
- On partial failure (commits unavailable), `contribution_streak` defaults to `0` with `success=True`

**Downstream effect:** `agent/orchestrator.py` stores tool results in `results["github_tool"]` and the new field will appear automatically in orchestrator output without orchestrator changes.

### Risks & unknowns

1. **GitHub API rate limits (`agent/tools/github_tool.py`, `_fetch_commit_dates`).** Unauthenticated requests cap at 60/hour; paginating commits for active repos could exhaust the budget. Mitigation: use `self.api_token` from env (`GITHUB_TOKEN` in `.env`) and cap pagination (e.g., stop after N pages or 365 days of history).

2. **Scope of "contribution history" (`agent/tools/github_tool.py`).** Issue wording suggests user-level activity, but the tool currently receives a single repo. I plan to compute streak from commits **in that repo** using `/repos/{owner}/{repo}/commits`.

3. **Timezone boundaries in `_calculate_longest_streak`.** GitHub returns ISO timestamps with timezone offsets. Two commits at 11pm and 1am UTC could span different local calendar days. Mitigation: normalize all dates to UTC before deduplication.

4. **Empty or fork-only repos.** A repo with zero commits or only initial commit should return `contribution_streak: 0` without raising an exception.

### Edge cases

1. **No commits in repo** - API returns `[]`; streak should be `0`.
2. **Single commit on one day** - streak should be `1`, not `0`.
3. **Non-consecutive commits** (e.g., Jan 1, Jan 3, Jan 4) - longest streak is `2` (Jan 3-4), not `3`.
4. **Multiple commits on the same day** - count as one day toward the streak (deduplicate dates before calculating).
5. **GitHub API 403/404 on commits endpoint** - return repo metadata successfully with `contribution_streak: 0` and log a warning, matching existing error-handling style in `execute()`.