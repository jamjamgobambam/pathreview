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
            has_tests=metadata["has_tests"],
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

    def _has_tests(self, username: str, repo_name: str, default_branch: str) -> bool:
        """Check whether the repository contains automated tests.

        Detects a ``tests/`` or ``test/`` directory, a ``pytest.ini`` file, or
        any file matching ``test_*.py`` anywhere in the repository tree. Uses the
        Git Trees API to read the full tree in a single request; if GitHub
        truncates the response (very large repos), falls back to checking the
        common top-level signals via the Contents API.

        Args:
            username: GitHub username
            repo_name: Repository name
            default_branch: The repository's default branch (e.g. "main")

        Returns:
            True if the repository appears to contain tests, else False.
        """
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        url = f"{self.base_url}/repos/{username}/{repo_name}/git/trees/{default_branch}"

        try:
            response = httpx.get(url, headers=headers, params={"recursive": "1"}, timeout=10.0)
            response.raise_for_status()
            tree_data = response.json()
        except Exception:
            # Missing branch, private repo, rate limit, or network error:
            # degrade gracefully rather than failing the whole analysis.
            return False

        tree = tree_data.get("tree", [])
        if self._tree_has_tests(tree):
            return True

        # GitHub omits entries when the tree is too large; probe the common
        # top-level signals directly so we do not report a false negative.
        if tree_data.get("truncated"):
            return self._has_tests_via_contents(username, repo_name, headers)

        return False

    @staticmethod
    def _tree_has_tests(tree: list[dict]) -> bool:
        """Return True if any entry in a git tree looks like a test artifact.

        Args:
            tree: The ``tree`` list from a Git Trees API response, where each
                entry has ``path`` and ``type`` keys.

        Returns:
            True if a test directory, ``pytest.ini``, or ``test_*.py`` file is found.
        """
        for entry in tree:
            path = entry.get("path", "")
            basename = path.rsplit("/", 1)[-1]

            # tests/ or test/ directory at any depth
            if entry.get("type") == "tree" and basename in ("tests", "test"):
                return True
            # pytest.ini anywhere
            if basename == "pytest.ini":
                return True
            # test_*.py files anywhere
            if basename.startswith("test_") and basename.endswith(".py"):
                return True
        return False

    def _has_tests_via_contents(
        self, username: str, repo_name: str, headers: dict[str, str]
    ) -> bool:
        """Fallback check for the common top-level test signals.

        Used when the Git Trees response is truncated. Checks for a top-level
        ``tests/`` or ``test/`` directory or a ``pytest.ini`` via the Contents API.

        Args:
            username: GitHub username
            repo_name: Repository name
            headers: Request headers (including auth) to reuse

        Returns:
            True if any of the top-level test signals exist, else False.
        """
        for path in ("tests", "test", "pytest.ini"):
            url = f"{self.base_url}/repos/{username}/{repo_name}/contents/{path}"
            try:
                response = httpx.head(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    return True
            except Exception:
                continue
        return False
