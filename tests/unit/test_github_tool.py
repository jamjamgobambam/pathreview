from agent.tools.github_tool import GitHubTool


def test_repo_metadata_contains_has_tests() -> None:
    """
    Reproduction test:
    Confirms that repository metadata is missing the expected
    has_tests field in the current implementation.
    """

    tool = GitHubTool()

    result = tool._fetch_repo_metadata("psf", "requests")

    assert "has_tests" in result, "Expected 'has_tests' field is missing"
