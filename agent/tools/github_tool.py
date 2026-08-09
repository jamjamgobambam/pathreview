"""GitHub repository metadata tool."""

from datetime import UTC, date, datetime, timedelta

import httpx
import structlog
from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class GitHubTool(BaseTool):
    """Fetch repository metadata from GitHub."""

    name = "github_tool"
    description = "Fetch repository metadata from GitHub"

    # The contributions calendar is only queryable one year at a time, so a full
    # history costs one request per year. Cap the lookback to bound that budget.
    MAX_LOOKBACK_YEARS = 5

    def __init__(self, api_token: str | None = None):
        """Initialize GitHub tool.

        Args:
            api_token: GitHub API token (optional for unauthenticated requests)
        """
        self.api_token = api_token
        self.base_url = "https://api.github.com"
        self.graphql_url = "https://api.github.com/graphql"

    def execute(self, input_data: dict) -> ToolResult:
        """Fetch GitHub repository metadata.

        Args:
            input_data: Must contain 'github_username' and 'repo_name'

        Returns:
            ToolResult with repository metadata
        """
        username = input_data.get("github_username")
        repo_name = input_data.get("repo_name")

        if not username or not repo_name:
            return ToolResult(
                success=False,
                data={},
                error="Missing github_username or repo_name"
            )

        try:
            repo_data = self._fetch_repo_metadata(username, repo_name)
            return ToolResult(success=True, data=repo_data)

        except httpx.HTTPStatusError as e:
            logger.error("github_request_failed", status=e.response.status_code,
                        username=username, repo=repo_name)
            if e.response.status_code == 404:
                return ToolResult(
                    success=False,
                    data={},
                    error="Repository not found"
                )
            elif e.response.status_code == 403:
                return ToolResult(
                    success=False,
                    data={},
                    error="Rate limited or access denied"
                )
            return ToolResult(
                success=False,
                data={},
                error=f"GitHub API error: {e.response.status_code}"
            )

        except Exception as e:
            logger.error("github_tool_error", error=str(e))
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )

    def _fetch_repo_metadata(self, username: str, repo_name: str) -> dict:
        """Fetch repository metadata from GitHub API.

        Args:
            username: GitHub username
            repo_name: Repository name

        Returns:
            Dict with repository metadata
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()

        repo_json = response.json()

        # Extract metadata, handling null values
        metadata = {
            "name": repo_json.get("name", ""),
            "description": repo_json.get("description") or "",
            "primary_language": repo_json.get("language") or "Unknown",
            "star_count": repo_json.get("stargazers_count", 0),
            "fork_count": repo_json.get("forks_count", 0),
            "open_issues_count": repo_json.get("open_issues_count", 0),
            "last_commit_date": repo_json.get("pushed_at", ""),
            "has_readme": self._has_readme(username, repo_name),
            "topics": repo_json.get("topics", []),
            "homepage": repo_json.get("homepage") or "",
            "contribution_streak": self._fetch_contribution_streak(username),
        }

        logger.info("github_repo_fetched", username=username, repo=repo_name,
                   language=metadata["primary_language"], stars=metadata["star_count"],
                   contribution_streak=metadata["contribution_streak"])

        return metadata

    def _has_readme(self, username: str, repo_name: str) -> bool:
        """Check if repository has a README file.

        Args:
            username: GitHub username
            repo_name: Repository name

        Returns:
            True if README exists
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}/readme"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        try:
            response = httpx.head(url, headers=headers, timeout=5.0)
            return bool(response.status_code == 200)
        except Exception:
            return False

    def _fetch_contribution_streak(self, username: str) -> int | None:
        """Compute the user's longest run of consecutive contributing days.

        Uses the GraphQL contributions calendar, which reports total daily
        contributions (commits, issues, PRs, reviews) and is the same data
        behind the green squares on a profile. The daily calendar is not
        exposed over REST, and /users/{u}/events only covers ~90 days.

        Requires an API token: the GraphQL endpoint rejects unauthenticated
        requests with 403, unlike the REST endpoints used elsewhere in this
        tool. Private contributions additionally need the `read:user` scope,
        without which the streak is silently undercounted.

        Args:
            username: GitHub username

        Returns:
            Longest streak in days, 0 if the user has never contributed, or
            None if the streak could not be measured (no token, API failure,
            or unknown user). None and 0 are deliberately distinct.
        """
        if not self.api_token:
            return None

        try:
            days = self._fetch_contribution_days(username)
        except Exception as e:
            logger.warning("github_streak_failed", username=username, error=str(e))
            return None

        if days is None:
            return None

        return self._longest_streak(days)

    def _fetch_contribution_days(self, username: str) -> dict[str, int] | None:
        """Collect date -> contribution count across the user's history.

        Walks backward in one-year windows because `to` defaults to one year
        past `from`, so a single query cannot span a full account history.
        Results are keyed by date, which deduplicates the overlapping days
        GraphQL returns at window edges (the calendar is week-aligned).

        Args:
            username: GitHub username

        Returns:
            Mapping of ISO date string to contribution count, or None if any
            window failed. A partial history would understate the streak, so
            a partial answer is never returned.
        """
        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            createdAt
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                weeks { contributionDays { date contributionCount } }
              }
            }
          }
        }
        """

        headers = {"Authorization": f"bearer {self.api_token}"}
        days: dict[str, int] = {}
        window_end = datetime.now(UTC)
        created_at: datetime | None = None

        for _ in range(self.MAX_LOOKBACK_YEARS):
            window_start = window_end - timedelta(days=365)

            response = httpx.post(
                self.graphql_url,
                json={
                    "query": query,
                    "variables": {
                        "login": username,
                        "from": window_start.isoformat(),
                        "to": window_end.isoformat(),
                    },
                },
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()

            body = response.json()
            if body.get("errors"):
                logger.warning("github_streak_graphql_errors", username=username)
                return None

            # A missing or renamed user comes back as data.user = null with a
            # 200 status, so raise_for_status() above will not catch it.
            user = (body.get("data") or {}).get("user")
            if not user:
                return None

            if created_at is None:
                created_at = datetime.fromisoformat(user["createdAt"])

            calendar = user["contributionsCollection"]["contributionCalendar"]
            for week in calendar["weeks"]:
                for day in week["contributionDays"]:
                    # max() so a zero-filled padding day at one window's edge
                    # cannot overwrite a real count from the adjacent window.
                    existing = days.get(day["date"], 0)
                    days[day["date"]] = max(existing, day["contributionCount"])

            if created_at is not None and window_start <= created_at:
                break

            window_end = window_start

        return days

    @staticmethod
    def _longest_streak(days: dict[str, int]) -> int:
        """Find the longest run of consecutive days with any contribution.

        Args:
            days: Mapping of ISO date string to contribution count

        Returns:
            Length of the longest consecutive run, 0 if there is none
        """
        longest = 0
        current = 0
        previous: date | None = None

        # ISO date strings sort chronologically, so a plain sort is enough.
        for day_str in sorted(days):
            if days[day_str] <= 0:
                continue

            day = date.fromisoformat(day_str)
            if previous is not None and (day - previous).days == 1:
                current += 1
            else:
                current = 1

            longest = max(longest, current)
            previous = day

        return longest
