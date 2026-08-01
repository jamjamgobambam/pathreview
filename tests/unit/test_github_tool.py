from agent.tools.github_tool import GitHubTool


def test_repo_metadata_contains_has_tests() -> None:
    """
    Verify repository metadata includes the has_tests field.
    """

    tool = GitHubTool()

    # Mock test detection to avoid making GitHub API calls
    tool._has_tests = lambda username, repo_name: True  # type: ignore[method-assign]

    result = tool._fetch_repo_metadata("psf", "requests")

    assert "has_tests" in result
    assert result["has_tests"] is True


def test_has_tests_returns_true_when_tests_exist() -> None:
    """
    Repository containing test files should return True.
    """

    tool = GitHubTool()

    tool._get_repo_tree = lambda username, repo_name: [  # type: ignore[method-assign]
        {"path": "src/main.py"},
        {"path": "tests/test_example.py"},
    ]

    result = tool._has_tests("owner", "repo")

    assert result is True


def test_has_tests_returns_true_for_pytest_configuration() -> None:
    """
    Repository containing pytest.ini should return True.
    """

    tool = GitHubTool()

    tool._get_repo_tree = lambda username, repo_name: [  # type: ignore[method-assign]
        {"path": "pytest.ini"},
        {"path": "src/main.py"},
    ]

    result = tool._has_tests("owner", "repo")

    assert result is True


def test_has_tests_returns_false_when_tests_are_missing() -> None:
    """
    Repository without test indicators should return False.
    """

    tool = GitHubTool()

    tool._get_repo_tree = lambda username, repo_name: [  # type: ignore[method-assign]
        {"path": "src/main.py"},
        {"path": "README.md"},
    ]

    result = tool._has_tests("owner", "repo")

    assert result is False


def test_has_tests_returns_false_when_api_fails() -> None:
    """
    GitHub API failures should safely return False.
    """

    tool = GitHubTool()

    def raise_error(username: str, repo_name: str) -> list[dict]:
        raise Exception("GitHub API unavailable")

    tool._get_repo_tree = raise_error  # type: ignore[method-assign]

    result = tool._has_tests("owner", "repo")

    assert result is False
