"""GitHub repository metadata tool."""

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

        default_branch = repo_json.get("default_branch", "main")
        repo_paths = self._fetch_repo_tree(
            username,
            repo_name,
            default_branch,
        )

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
            "has_tests": self._has_tests(repo_paths),
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

    def _has_tests(self, paths: list[str]) -> bool:
        """Check whether repository paths contain common test indicators.

        Args:
            paths: Repository file and directory paths.

        Returns:
            True if recognized tests are present, otherwise False.
        """
        for path in paths:
            normalized_path = path.strip("/").lower()
            parts = normalized_path.split("/")
            filename = parts[-1]

            if "tests" in parts or "test" in parts:
                return True

            if filename == "pytest.ini":
                return True

            if filename.startswith("test_") and filename.endswith(".py"):
                return True

        return False

    def _fetch_repo_tree(
        self,
        username: str,
        repo_name: str,
        branch: str,
    ) -> list[str]:
        """Fetch repository file and directory paths from GitHub.

        Args:
            username: GitHub username.
            repo_name: Repository name.
            branch: Repository branch to inspect.

        Returns:
            Repository file and directory paths.
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}" f"/git/trees/{branch}"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        response = httpx.get(
            url,
            headers=headers,
            params={"recursive": "1"},
            timeout=10.0,
        )
        response.raise_for_status()

        tree_json = response.json()

        if tree_json.get("truncated", False):
            logger.warning(
                "github_tree_truncated",
                username=username,
                repo=repo_name,
                branch=branch,
            )

        return [item["path"] for item in tree_json.get("tree", []) if item.get("path")]
