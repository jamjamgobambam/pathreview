"""GitHub repository metadata tool."""

from datetime import date, timedelta

import httpx
import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class GitHubTool(BaseTool):
    """Fetch repository metadata from GitHub."""

    name = "github_tool"
    description = "Fetch repository metadata from GitHub"

    def __init__(self, api_token: str | None = None):
        """Initialize GitHub tool.

        Args:
            api_token: GitHub API token (optional for unauthenticated requests)
        """
        self.api_token = api_token
        self.base_url = "https://api.github.com"

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
            return ToolResult(success=False, data={}, error="Missing github_username or repo_name")

        try:
            repo_data = self._fetch_repo_metadata(username, repo_name)
            return ToolResult(success=True, data=repo_data)

        except httpx.HTTPStatusError as e:
            logger.error(
                "github_request_failed",
                status=e.response.status_code,
                username=username,
                repo=repo_name,
            )
            if e.response.status_code == 404:
                return ToolResult(success=False, data={}, error="Repository not found")
            elif e.response.status_code == 403:
                return ToolResult(success=False, data={}, error="Rate limited or access denied")
            return ToolResult(
                success=False, data={}, error=f"GitHub API error: {e.response.status_code}"
            )

        except Exception as e:
            logger.error("github_tool_error", error=str(e))
            return ToolResult(success=False, data={}, error=str(e))

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
            "contribution_streak": self._longest_contribution_streak(username),
        }

        logger.info(
            "github_repo_fetched",
            username=username,
            repo=repo_name,
            language=metadata["primary_language"],
            stars=metadata["star_count"],
        )

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
            return response.status_code == 200
        except Exception:
            return False

    def _longest_contribution_streak(self, username: str) -> int:
        """Compute the longest run of consecutive days with GitHub activity.

        Uses the GraphQL contributionsCollection API, which reports
        account-wide contributions (commits, PRs, issues, reviews) rather
        than commits to a single repo. This requires an authenticated
        request, and the API only reports the trailing 365 days of
        activity, so streaks that started more than a year ago will be
        undercounted.

        Args:
            username: GitHub username

        Returns:
            Longest run of consecutive days with at least one contribution.
            0 if there's no token to authenticate with, the user doesn't
            exist, or the user has no contributions in the last year.
        """
        if not self.api_token:
            return 0

        query = """
        query($username: String!) {
          user(login: $username) {
            contributionsCollection {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """

        headers = {"Authorization": f"Bearer {self.api_token}"}

        try:
            response = httpx.post(
                f"{self.base_url}/graphql",
                json={"query": query, "variables": {"username": username}},
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()

            user_data = payload.get("data", {}).get("user")
            if payload.get("errors") or not user_data:
                return 0

            weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
            active_days = {
                date.fromisoformat(day["date"])
                for week in weeks
                for day in week["contributionDays"]
                if day["contributionCount"] > 0
            }

            if not active_days:
                return 0

            sorted_days = sorted(active_days)
            longest = current = 1
            for previous_day, day in zip(sorted_days, sorted_days[1:], strict=False):
                if day - previous_day == timedelta(days=1):
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 1

            return longest

        except Exception as e:
            logger.error("github_contribution_streak_error", username=username, error=str(e))
            return 0
