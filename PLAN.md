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

1. Inspect the existing GitHub tests and determine how GitHub API responses are mocked.
2. Add a method that retrieves the user's commit or contribution dates from GitHub.
3. Add a helper method that removes duplicate dates, sorts the dates, and calculates the longest consecutive-day streak.
4. Add the calculated value to the GitHub analysis output as `contribution_streak`.
5. Add tests for normal behavior, missing contribution data, duplicate dates, unsorted dates, and gaps between contribution days.

### Inputs & outputs

The existing tool takes:

```python
{
    "github_username": "username",
    "repo_name": "repository"
}
```

The fix will continue using the GitHub username to retrieve contribution activity.

The output should keep all existing repository metadata and add:

```python
{
    "contribution_streak": 5
}
```

The value should be an integer representing the user's longest sequence of consecutive commit days.

Multiple commits on the same day should count as one contribution day.

### Risks & unknowns

- The current repository API endpoint does not provide contribution history, so another GitHub API request will be required.
- It is not yet confirmed whether the maintainers expect user-wide GitHub activity or commits only from the selected repository.
- GitHub's contribution calendar may require an authenticated GraphQL request.
- GitHub API pagination could cause an incorrect streak if only part of the commit history is retrieved.
- Private contributions may not be available depending on the API token permissions.
- Time zones may affect which calendar day a commit belongs to.
- I need to confirm whether a contribution-history request failure should fail the entire tool or leave the streak unavailable.

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
