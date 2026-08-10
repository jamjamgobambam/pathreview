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
        default_branch = repo_json.get("default_branch") or "main"
        files = self._fetch_file_tree(username, repo_name, default_branch)

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
            "files": files,
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

    def _fetch_file_tree(self, username: str, repo_name: str, default_branch: str) -> list[str]:
        """Fetch a flat file tree for the repository's default branch.

        Args:
            username: GitHub username
            repo_name: Repository name
            default_branch: Repository default branch name

        Returns:
            Flat list of file paths, or an empty list on failure
        """
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        try:
            branch_url = f"{self.base_url}/repos/{username}/{repo_name}/branches/{default_branch}"
            branch_response = httpx.get(branch_url, headers=headers, timeout=10.0)
            branch_response.raise_for_status()

            branch_json = branch_response.json()
            tree_sha = branch_json.get("commit", {}).get("commit", {}).get("tree", {}).get("sha")
            if not tree_sha:
                return []

            tree_url = f"{self.base_url}/repos/{username}/{repo_name}/git/trees/{tree_sha}"
            tree_response = httpx.get(
                tree_url,
                headers=headers,
                params={"recursive": "1"},
                timeout=10.0,
            )
            tree_response.raise_for_status()

            tree_json = tree_response.json()
            tree_entries = tree_json.get("tree", [])
            files = [
                entry.get("path", "")
                for entry in tree_entries
                if entry.get("type") == "blob" and entry.get("path")
            ]

            if tree_json.get("truncated"):
                logger.warning(
                    "github_tree_truncated",
                    username=username,
                    repo=repo_name,
                    file_count=len(files),
                )

            return files

        except Exception as e:
            logger.warning(
                "github_file_tree_fetch_failed",
                username=username,
                repo=repo_name,
                error=str(e),
            )
            return []

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
