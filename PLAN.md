## Solution plan

**Issue:** [Add a contribution_streak field to the GitHub analysis](https://github.com/ascherj/pathreview/issues/52)

### Understand

The current `GitHubTool` retrieves metadata for one repository through the GitHub REST API. It returns fields such as the repository name, primary language, stars, forks, open issues, last push date, README status, topics, and homepage.

The tool does not currently retrieve the user's contribution history. Because the contribution dates are not available, it cannot calculate the user's longest sequence of consecutive commit days.

The expected behavior is for the GitHub analysis to include a `contribution_streak` field containing the longest number of consecutive days on which the user made commits.

### Map

The main file involved is:

- `agent/tools/github_tool.py`

The relevant functions are:

- `GitHubTool.execute()`
- `GitHubTool._fetch_repo_metadata()`

I also expect to inspect and update the GitHub-related tests under:

- `tests/`

The exact test file will be confirmed by searching the existing test suite for `GitHubTool`.

### Plan

1. Add focused unit tests for the GitHub tool and mock its HTTP requests with `unittest.mock`.
2. Use GraphQL `commitContributionsByRepository` to retrieve the user's commit dates from the previous year.
3. Collect each commit contribution's `occurredAt` date across the returned repositories.
4. Add a helper that removes duplicate dates, sorts them, and calculates the longest consecutive-day streak.
5. Add the calculated value to the existing GitHub metadata as `contribution_streak`.
6. Return an unsuccessful `ToolResult` when the contribution request fails or GraphQL returns errors.

### Inputs & outputs

The existing tool takes:

```python
{
    "github_username": "username",
    "repo_name": "repository"
}
```

The fix will continue using the GitHub username to retrieve user-wide commit activity. The repository name will still be used for the existing metadata request.

The output should keep all existing repository metadata and add:

```python
{
    "contribution_streak": 5
}
```

The value should be an integer representing the user's longest sequence of consecutive commit days.

Multiple commits on the same day should count as one contribution day.

### Design decisions and limits

- The issue asks for the user's GitHub contribution history, so the streak will be user-wide instead of limited to `repo_name`.
- `commitContributionsByRepository` returns commit-only contribution dates grouped by repository.
- The query covers the previous year. Fetching the user's full account history is outside this issue's current scope.
- Repository groups and commit-day connections must not be silently truncated.
- GraphQL requires `api_token`. A missing token will return an unsuccessful result instead of using zero.
- Private commit data depends on the token permissions.
- The calculation will use each commit contribution's GitHub date without changing time zones.
- A successful response with no commit days will return zero.
- HTTP failures and GraphQL errors will fail the whole tool instead of returning zero.

### Edge cases

The fix should handle:

- no commit or contribution dates
- one contribution day
- multiple commits on the same day
- duplicate contribution dates
- unsorted dates
- separate streaks with gaps
- contributions across month boundaries
- contributions across year boundaries
- leap-year dates
- GitHub API errors
- rate-limit responses
- users with no public contribution history
