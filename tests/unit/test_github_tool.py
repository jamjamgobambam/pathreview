"""Unit tests for GitHubTool."""

from unittest.mock import Mock, patch

import httpx
import pytest

from agent.tools.github_tool import GitHubTool


@pytest.fixture
def github_tool() -> GitHubTool:
    """Return a GitHubTool instance for testing."""
    return GitHubTool()


@pytest.mark.parametrize(
    "test_path",
    [
        "tests/test_example.py",
        "test/test_example.py",
        "pytest.ini",
        "src/test_service.py",
    ],
)
def test_execute_detects_repository_tests(
    github_tool: GitHubTool,
    test_path: str,
) -> None:
    """Test recognized test paths set has_tests to True."""
    repo_response = Mock()
    repo_response.raise_for_status.return_value = None
    repo_response.json.return_value = {
        "name": "example-repo",
        "description": "Example repository",
        "language": "Python",
        "stargazers_count": 1,
        "forks_count": 2,
        "open_issues_count": 3,
        "pushed_at": "2026-08-04T00:00:00Z",
        "default_branch": "main",
        "topics": [],
        "homepage": None,
    }

    tree_response = Mock()
    tree_response.raise_for_status.return_value = None
    tree_response.json.return_value = {
        "tree": [
            {"path": "README.md", "type": "blob"},
            {"path": test_path, "type": "blob"},
        ]
    }

    readme_response = Mock()
    readme_response.status_code = 200

    with (
        patch(
            "agent.tools.github_tool.httpx.get",
            side_effect=[repo_response, tree_response],
        ),
        patch(
            "agent.tools.github_tool.httpx.head",
            return_value=readme_response,
        ),
    ):
        result = github_tool.execute(
            {
                "github_username": "example-user",
                "repo_name": "example-repo",
            }
        )

    assert result.success is True
    assert result.error is None
    assert result.data["has_tests"] is True


def test_execute_returns_false_when_repository_has_no_tests(
    github_tool: GitHubTool,
) -> None:
    """Test repositories without test indicators return False."""
    repo_response = Mock()
    repo_response.raise_for_status.return_value = None
    repo_response.json.return_value = {
        "name": "example-repo",
        "description": "Example repository",
        "language": "Python",
        "stargazers_count": 1,
        "forks_count": 2,
        "open_issues_count": 3,
        "pushed_at": "2026-08-04T00:00:00Z",
        "default_branch": "main",
        "topics": [],
        "homepage": None,
    }

    tree_response = Mock()
    tree_response.raise_for_status.return_value = None
    tree_response.json.return_value = {
        "tree": [
            {"path": "README.md", "type": "blob"},
            {"path": "src/main.py", "type": "blob"},
            {"path": "requirements.txt", "type": "blob"},
        ]
    }

    readme_response = Mock()
    readme_response.status_code = 200

    with (
        patch(
            "agent.tools.github_tool.httpx.get",
            side_effect=[repo_response, tree_response],
        ),
        patch(
            "agent.tools.github_tool.httpx.head",
            return_value=readme_response,
        ),
    ):
        result = github_tool.execute(
            {
                "github_username": "example-user",
                "repo_name": "example-repo",
            }
        )

    assert result.success is True
    assert result.data["has_tests"] is False


def test_execute_returns_false_when_tree_request_fails(
    github_tool: GitHubTool,
) -> None:
    """Test failed tree requests safely return has_tests False."""
    repo_response = Mock()
    repo_response.raise_for_status.return_value = None
    repo_response.json.return_value = {
        "name": "example-repo",
        "description": "Example repository",
        "language": "Python",
        "stargazers_count": 1,
        "forks_count": 2,
        "open_issues_count": 3,
        "pushed_at": "2026-08-04T00:00:00Z",
        "default_branch": "main",
        "topics": [],
        "homepage": None,
    }

    request = httpx.Request(
        "GET",
        "https://api.github.com/repos/example-user/example-repo/git/trees/main",
    )
    failed_response = httpx.Response(404, request=request)
    tree_error = httpx.HTTPStatusError(
        "Tree request failed",
        request=request,
        response=failed_response,
    )

    readme_response = Mock()
    readme_response.status_code = 200

    with (
        patch(
            "agent.tools.github_tool.httpx.get",
            side_effect=[repo_response, tree_error],
        ),
        patch(
            "agent.tools.github_tool.httpx.head",
            return_value=readme_response,
        ),
    ):
        result = github_tool.execute(
            {
                "github_username": "example-user",
                "repo_name": "example-repo",
            }
        )

    assert result.success is True
    assert result.data["has_tests"] is False
