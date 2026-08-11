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

    # Bound the commit-history fetch used for the contribution streak so a
    # large/active repo can't blow the rate limit or hang: only look back
    # 12 months, and cap pagination as a hard backstop on top of that.
    COMMITS_LOOKBACK_DAYS = 365
    MAX_COMMIT_PAGES = 20

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
            "contribution_streak": self._fetch_contribution_streak(username, repo_name),
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

    def _fetch_contribution_streak(self, username: str, repo_name: str) -> int:
        """Compute the longest streak of consecutive days with a commit.

        Fetches commit history and derives the streak from it. GitHub
        outages, rate limiting, or unexpected response shapes here
        shouldn't take down the rest of the metadata this tool already
        fetched successfully, so any failure degrades to a streak of 0
        rather than propagating.

        Args:
            username: GitHub username (used to filter commit authorship)
            repo_name: Repository name

        Returns:
            Longest run of consecutive calendar days with at least one
            commit by `username`, or 0 if it couldn't be determined.
        """
        try:
            commit_dates = self._fetch_commit_dates(username, repo_name)
            return self._compute_contribution_streak(commit_dates)
        except Exception as e:
            logger.warning(
                "contribution_streak_fetch_failed",
                username=username,
                repo=repo_name,
                error=str(e),
            )
            return 0

    def _fetch_commit_dates(self, username: str, repo_name: str) -> list[date]:
        """Fetch calendar dates of commits authored by `username` in a repo.

        Paginates through `GET /repos/{owner}/{repo}/commits`, filtered by
        author and bounded to the last `COMMITS_LOOKBACK_DAYS` days. As a
        backstop against very active repos, pagination also stops after
        `MAX_COMMIT_PAGES` pages regardless of lookback window.

        Uses each commit's author date (not committer date) since that
        reflects when the person actually made the change, rather than
        when it was later applied (e.g. via rebase or cherry-pick).

        Args:
            username: GitHub username
            repo_name: Repository name

        Returns:
            List of commit dates (UTC calendar day), one per commit,
            possibly containing duplicates for multiple same-day commits.
        """
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        since = (datetime.now(UTC) - timedelta(days=self.COMMITS_LOOKBACK_DAYS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        url = f"{self.base_url}/repos/{username}/{repo_name}/commits"
        params: dict | None = {"author": username, "per_page": 100, "since": since}

        commit_dates: list[date] = []
        page = 0
        while url and page < self.MAX_COMMIT_PAGES:
            response = httpx.get(url, headers=headers, params=params, timeout=10.0)
            response.raise_for_status()

            for commit in response.json():
                date_str = commit.get("commit", {}).get("author", {}).get("date")
                if date_str:
                    commit_dates.append(
                        datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
                    )

            url = response.links.get("next", {}).get("url")
            params = None  # `next` URL from the Link header already includes query params
            page += 1

        return commit_dates

    def _compute_contribution_streak(self, commit_dates: list[date]) -> int:
        """Compute the longest run of consecutive calendar days.

        Args:
            commit_dates: Commit dates, possibly with duplicates/unsorted

        Returns:
            Longest streak of consecutive days present in `commit_dates`,
            or 0 if the list is empty.
        """
        if not commit_dates:
            return 0

        unique_dates = sorted(set(commit_dates))

        longest = 1
        current = 1
        for previous_date, current_date in zip(unique_dates, unique_dates[1:], strict=False):
            if (current_date - previous_date).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest
