"""GitHub repository metadata tool."""

import httpx
import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class GitHubTool(BaseTool):
    """Fetch repository metadata from GitHub."""

    name = "github_tool"
    description = "Fetch repository metadata from GitHub"

    # Directory and file names that indicate a repository ships tests. These are
    # matched against whole path segments rather than raw substrings, so paths
    # like "contest/" or "latest/" do not register as test markers.
    TEST_DIR_NAMES = frozenset({"tests", "test"})
    TEST_FILE_NAMES = frozenset({"pytest.ini"})

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
            # Pass the default branch we already have from repo_json so the tree
            # lookup does not have to re-fetch it; fall back to "main" if absent.
            "has_tests": self._has_tests(
                username, repo_name, repo_json.get("default_branch") or "main"
            ),
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

    @classmethod
    def _path_indicates_tests(cls, path: str) -> bool:
        """Check if a single repository path is a test marker.

        A path counts as a test marker when it lives under a ``tests/`` or
        ``test/`` directory, is a known test config file such as ``pytest.ini``,
        or is a Python test module named ``test_*.py``.

        Args:
            path: Repository-relative path, e.g. ``tests/unit/test_foo.py``

        Returns:
            True if the path indicates the presence of tests
        """
        if not path:
            return False

        segments = [segment.lower() for segment in path.split("/")]

        if cls.TEST_DIR_NAMES.intersection(segments):
            return True

        filename = segments[-1]
        if filename in cls.TEST_FILE_NAMES:
            return True

        return filename.startswith("test_") and filename.endswith(".py")

    def _has_tests(self, username: str, repo_name: str, default_branch: str = "main") -> bool:
        """Check if repository contains tests.

        Reads the repository file tree and looks for any test marker: a
        ``tests/`` or ``test/`` directory, a ``pytest.ini``, or a file matching
        ``test_*.py``.

        Args:
            username: GitHub username
            repo_name: Repository name
            default_branch: Branch whose file tree is inspected

        Returns:
            True if a test marker is found. False if none is found or the file
            tree cannot be read.
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}/git/trees/{default_branch}"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        try:
            response = httpx.get(url, headers=headers, params={"recursive": "1"}, timeout=10.0)
            response.raise_for_status()
            tree_json = response.json()
        except Exception:
            # Test detection is best-effort: a missing branch, a rate limit, or a
            # network failure must never break repository analysis.
            logger.debug("github_tree_fetch_failed", username=username, repo=repo_name)
            return False

        # Guard the shape before iterating: an unexpected payload should report
        # "no tests found" rather than raise from inside the loop below.
        tree = tree_json.get("tree", [])
        if not isinstance(tree, list):
            return False

        # One marker anywhere in the tree is enough, so stop at the first hit.
        for entry in tree:
            if self._path_indicates_tests(entry.get("path", "")):
                return True

        # The Git Trees API truncates very large repositories ("truncated": true).
        # Detection can under-report there; paginating the tree is out of scope.
        if tree_json.get("truncated"):
            logger.debug("github_tree_truncated", username=username, repo=repo_name)

        return False
