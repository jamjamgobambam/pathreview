"""GitHub repository metadata tool."""

from datetime import date, datetime, timedelta

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
        try:
            commit_dates = self._fetch_commit_dates(username, repo_name)
            streak = self._calculate_longest_streak(commit_dates)
        except Exception as e:
            logger.warning(
                "github_commits_fetch_failed",
                error=str(e),
                username=username,
                repo=repo_name,
            )
            streak = 0
        metadata = {
            "name": repo_json.get("name", ""),
            "contribution_streak": streak,
            "description": repo_json.get("description") or "",
            "primary_language": repo_json.get("language") or "Unknown",
            "star_count": repo_json.get("stargazers_count", 0),
            "fork_count": repo_json.get("forks_count", 0),
            "open_issues_count": repo_json.get("open_issues_count", 0),
            "last_commit_date": repo_json.get("pushed_at", ""),
            "has_readme": self._has_readme(username, repo_name),
            "topics": repo_json.get("topics", []),
            "homepage": repo_json.get("homepage") or "",
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
            return bool(response.status_code == 200)
        except Exception:
            return False

    def _fetch_commit_dates(self, username: str, repo_name: str) -> list[date]:
        """Fetch commit dates from GitHub commits API.

        Args:
            username: GitHub username
            repo_name: Repository name

        Returns:
            List of UTC calendar dates when commits were made
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}/commits"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        dates: list[date] = []
        page = 1
        max_pages = 10

        while page <= max_pages:
            response = httpx.get(
                url,
                headers=headers,
                params={"page": page, "per_page": 100},
                timeout=10.0,
            )
            response.raise_for_status()
            commits = response.json()

            if not commits:
                break

            for commit in commits:
                date_str = commit["commit"]["author"]["date"]
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dates.append(dt.date())

            page += 1

        return dates

    def _calculate_longest_streak(self, dates: list[date]) -> int:
        """Find the longest run of consecutive calendar days with commits.
        Args:
            dates: List of commit dates (may contain duplicates)
        Returns:
            Longest consecutive-day streak (0 if no dates)
        """
        if not dates:
            return 0
        unique_dates = sorted(set(dates))
        longest = 1
        current = 1
        for i in range(1, len(unique_dates)):
            if unique_dates[i] - unique_dates[i - 1] == timedelta(days=1):
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        return longest
