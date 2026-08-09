"""GitHub repository metadata tool."""

from urllib.parse import quote

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
        default_branch = repo_json.get("default_branch")
        if not isinstance(default_branch, str) or not default_branch:
            raise ValueError("GitHub repository metadata is missing a default branch")

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
            "has_tests": self._has_tests(username, repo_name, default_branch),
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
            return response.status_code == 200
        except Exception:
            return False

    def _has_tests(self, username: str, repo_name: str, default_branch: str) -> bool:
        """Check whether a repository tree contains a supported test indicator.

        Args:
            username: GitHub username.
            repo_name: Repository name.
            default_branch: Repository default branch.

        Returns:
            True when the tree contains a tests/test directory, pytest.ini, or
            a Python file whose basename starts with test_.

        Raises:
            ValueError: If GitHub returns an incomplete or malformed tree.
            httpx.HTTPStatusError: If the tree request fails.
        """
        encoded_branch = quote(default_branch, safe="")
        url = (
            f"{self.base_url}/repos/{username}/{repo_name}"
            f"/git/trees/{encoded_branch}?recursive=1"
        )

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        tree_json = response.json()

        if not isinstance(tree_json, dict) or tree_json.get("truncated") is True:
            raise ValueError("GitHub repository tree is unavailable or truncated")

        tree = tree_json.get("tree")
        if not isinstance(tree, list):
            raise ValueError("GitHub repository tree response is malformed")

        for entry in tree:
            if not isinstance(entry, dict):
                raise ValueError("GitHub repository tree response is malformed")

            path = entry.get("path")
            entry_type = entry.get("type")
            if not isinstance(path, str) or not isinstance(entry_type, str):
                raise ValueError("GitHub repository tree response is malformed")

            if self._is_test_path(path, entry_type):
                return True

        return False

    @staticmethod
    def _is_test_path(path: str, entry_type: str) -> bool:
        """Return whether a Git tree entry matches an issue #50 indicator.

        Args:
            path: Repository-relative path.
            entry_type: Git tree entry type, such as ``tree`` or ``blob``.

        Returns:
            True when the path is a supported test indicator.
        """
        parts = [part for part in path.split("/") if part]
        if not parts:
            return False

        directory_parts = parts if entry_type == "tree" else parts[:-1]
        if any(part in {"test", "tests"} for part in directory_parts):
            return True

        basename = parts[-1]
        return basename == "pytest.ini" or (
            entry_type == "blob" and basename.startswith("test_") and basename.endswith(".py")
        )
